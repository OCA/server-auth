# Copyright 2026 Lorenzo Battistini
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase, tagged

from odoo.addons.auth_jwt.exceptions import UnauthorizedInvalidToken

from ..exceptions import InsufficientScope, OAuthError
from . import common


@tagged("post_install", "-at_install")
class TestResource(common.OAuthServerMixin, TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.setup_oauth_server()

    def test_resource_creates_its_validator(self):
        validator = self.resource.jwt_validator_id
        self.assertEqual(validator.name, "oauth_server_test_api")
        self.assertEqual(validator.user_id_strategy, "oauth_server")
        self.assertEqual(validator.signature_type, "secret")
        self.assertTrue(validator.secret_key)
        self.assertFalse(validator.cookie_enabled)
        self.assertEqual(validator.issuer, common.ISSUER)
        self.assertEqual(validator.audience, common.ISSUER + "/test_api")
        self.assertEqual(self.resource.uri, common.ISSUER + "/test_api")
        other = self.env["oauth.server.resource"].create(
            {"name": "Other", "path": "/test-api"}
        )
        self.assertEqual(other.jwt_validator_id.name, "oauth_server_test_api_2")

    def test_root_resource(self):
        resource = self.env["oauth.server.resource"].create(
            {"name": "Root", "path": "/"}
        )
        self.assertEqual(resource.uri, common.ISSUER)
        self.assertEqual(resource.jwt_validator_id.name, "oauth_server_root")
        self.assertEqual(
            resource._get_metadata_url(),
            common.ISSUER + "/.well-known/oauth-protected-resource",
        )

    def test_invalid_path(self):
        for path in ("api", "/api/", "/api?x=1", "/a b"):
            with self.assertRaises(ValidationError, msg=path):
                self.env["oauth.server.resource"].create({"name": "X", "path": path})

    def test_validator_follows_issuer_and_path(self):
        settings = self.env["res.config.settings"].create(
            {"oauth_server_issuer": "https://new.example.com/"}
        )
        settings.set_values()
        params = self.env["ir.config_parameter"].sudo()
        self.assertEqual(
            params.get_param("auth_oauth_server.issuer"), "https://new.example.com"
        )
        validator = self.resource.jwt_validator_id
        self.assertEqual(validator.issuer, "https://new.example.com")
        self.assertEqual(validator.audience, "https://new.example.com/test_api")
        self.resource.path = "/renamed"
        self.assertEqual(validator.audience, "https://new.example.com/renamed")

    def test_unlink_removes_validator(self):
        validator = self.resource.jwt_validator_id
        self.resource.unlink()
        self.assertFalse(validator.exists())

    def test_unnamed_jwt_routes_ignore_oauth_validators(self):
        """auth="jwt" routes need exactly one validator: those of the
        authorization server must not count."""
        validators = self.env["auth.jwt.validator"]
        domain = validators._get_validator_by_name_domain(None)
        self.assertNotIn(self.resource.jwt_validator_id, validators.search(domain))
        by_name = validators._get_validator_by_name("oauth_server_test_api")
        self.assertEqual(by_name, self.resource.jwt_validator_id)

    def test_scopes(self):
        self.assertEqual(self.resource._filter_scopes("write"), "write")
        self.assertEqual(self.resource._filter_scopes("write read write"), "write read")
        # unknown scopes are dropped rather than refused (RFC 6749 3.3)
        self.assertEqual(self.resource._filter_scopes("admin write"), "write")
        self.assertEqual(self.resource._filter_scopes("admin"), "read write")
        self.assertEqual(self.resource._filter_scopes(None), "read write")

    def test_resource_from_request(self):
        resources = self.env["oauth.server.resource"]
        for uri in (
            common.ISSUER + "/test_api",
            common.ISSUER.upper() + "/test_api/",
        ):
            self.assertEqual(resources._get_for_request(uri), self.resource)
        with self.assertRaises(OAuthError) as error:
            resources._get_for_request(common.ISSUER + "/unknown")
        self.assertEqual(error.exception.error, "invalid_target")
        resources.create({"name": "Second", "path": "/second"})
        with self.assertRaises(OAuthError) as error:
            resources._get_for_request(None)
        self.assertEqual(error.exception.error, "invalid_target")

    def test_allowed_users(self):
        portal = self.env["res.users"].create(
            {
                "name": "Portal",
                "login": "oauth_portal",
                "groups_id": [(6, 0, [self.env.ref("base.group_portal").id])],
            }
        )
        self.assertTrue(self.resource._is_user_allowed(self.user))
        self.assertFalse(self.resource._is_user_allowed(portal))
        group = self.env["res.groups"].create({"name": "API users"})
        self.resource.group_ids = group
        self.assertFalse(self.resource._is_user_allowed(self.user))
        group.users = self.user
        self.assertTrue(self.resource._is_user_allowed(self.user))
        self.user.active = False
        self.assertFalse(self.resource._is_user_allowed(self.user))

    def test_metadata(self):
        self.assertEqual(
            self.resource._metadata(),
            {
                "resource": common.ISSUER + "/test_api",
                "authorization_servers": [common.ISSUER],
                "scopes_supported": ["read", "write"],
                "bearer_methods_supported": ["header"],
                "resource_name": "Test API",
            },
        )

    def test_www_authenticate(self):
        metadata_url = common.ISSUER + "/.well-known/oauth-protected-resource/test_api"
        self.assertEqual(
            self.resource._www_authenticate(),
            'Bearer resource_metadata="%s", scope="read write"' % metadata_url,
        )
        self.assertEqual(
            self.resource._www_authenticate(
                error="invalid_token", error_description='a "quoted" text', scope=""
            ),
            'Bearer resource_metadata="%s", error="invalid_token", '
            'error_description="a \\"quoted\\" text"' % metadata_url,
        )

    def test_authenticate_bearer(self):
        _authorization, tokens = self.tokens()
        uid, payload = self.resource._authenticate_bearer(
            tokens["access_token"], ["read"]
        )
        self.assertEqual(uid, self.user.id)
        self.assertEqual(payload["scope"], "read write")
        with self.assertRaises(InsufficientScope) as error:
            self.resource._authenticate_bearer(tokens["access_token"], ["admin"])
        self.assertEqual(error.exception.scope, "admin")
        with self.assertRaises(UnauthorizedInvalidToken):
            self.resource._authenticate_bearer("not.a.token")

    def test_rotate_secret(self):
        _authorization, tokens = self.tokens()
        self.resource.action_rotate_secret()
        with self.assertRaises(UnauthorizedInvalidToken):
            self.check_token(tokens["access_token"])
        # the refresh token still works and yields a token with the new secret
        tokens = self.refresh(tokens["refresh_token"])
        self.assertEqual(self.check_token(tokens["access_token"]), self.user.id)
