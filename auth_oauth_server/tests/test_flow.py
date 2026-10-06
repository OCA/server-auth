# Copyright 2026 Lorenzo Battistini
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from datetime import timedelta

import jwt  # pylint: disable=missing-manifest-dependency

from odoo import fields
from odoo.exceptions import AccessError
from odoo.tests.common import TransactionCase, new_test_user, tagged

from odoo.addons.auth_jwt.exceptions import UnauthorizedInvalidToken

from ..exceptions import OAuthError
from . import common


@tagged("post_install", "-at_install")
class TestFlow(common.OAuthServerMixin, TransactionCase):
    """The authorization code flow, model side."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.setup_oauth_server()

    def assertOAuthError(self, error, function, *args, **kwargs):
        with self.assertRaises(OAuthError) as raised:
            function(*args, **kwargs)
        self.assertEqual(raised.exception.error, error, raised.exception.description)
        return raised.exception

    def assertOAuthErrorKeepingChanges(self, error, function, *args, **kwargs):
        """assertOAuthError without the savepoint that Odoo's assertRaises
        rolls back: the controllers keep what the model did before failing."""
        try:
            function(*args, **kwargs)
        except OAuthError as raised:
            self.assertEqual(raised.error, error, raised.description)
        else:
            self.fail("%s not raised" % error)

    # ------------------------------------------------------------------
    # Authorization request
    # ------------------------------------------------------------------

    def request_params(self, **params):
        _verifier, challenge = common.pkce_pair()
        return dict(
            {
                "client_id": self.client.identifier,
                "redirect_uri": common.REDIRECT_URI,
                "response_type": "code",
                "code_challenge": challenge,
                "code_challenge_method": "S256",
                "resource": self.resource.uri,
                "scope": "read",
                "state": "xyz",
            },
            **params
        )

    def test_authorization_request(self):
        server = self.env["oauth.server"]
        params = self.request_params()
        client, redirect_uri = server._get_authorization_client(params)
        self.assertEqual(client, self.client)
        values = server._check_authorization_request(
            client, redirect_uri, params, self.user
        )
        self.assertEqual(values["resource"], self.resource.id)
        self.assertEqual(values["scope"], "read")
        self.assertEqual(values["uid"], self.user.id)
        self.assertEqual(values["state"], "xyz")
        verified = server._verify_consent(server._sign_consent(values))
        verified.pop("exp")
        self.assertEqual(verified, values)
        code = server._approve(values, self.user)
        authorization = self.env["oauth.server.authorization"].search(
            [("user_id", "=", self.user.id)]
        )
        self.assertEqual(len(authorization), 1)
        self.assertEqual(authorization.state, "pending")
        self.assertTrue(code)

    def test_authorization_request_client_errors(self):
        server = self.env["oauth.server"]
        for params in (
            self.request_params(client_id=None),
            self.request_params(client_id="unknown"),
            self.request_params(redirect_uri="https://evil.example.com/callback"),
            self.request_params(redirect_uri=common.REDIRECT_URI + "/"),
            self.request_params(redirect_uri=None),
        ):
            with self.assertRaises(OAuthError):
                server._get_authorization_client(params)
        self.client.active = False
        self.assertOAuthError(
            "unauthorized_client",
            server._get_authorization_client,
            self.request_params(),
        )

    def test_authorization_request_redirect_uri(self):
        server = self.env["oauth.server"]
        _client, redirect_uri = server._get_authorization_client(
            self.request_params(redirect_uri="http://127.0.0.1:43123/callback")
        )
        self.assertEqual(redirect_uri, "http://127.0.0.1:43123/callback")
        # the only registered redirect URI is the default
        _client, redirect_uri = server._get_authorization_client(
            self.request_params(
                client_id=self.confidential_client.identifier, redirect_uri=None
            )
        )
        self.assertEqual(redirect_uri, common.REDIRECT_URI)

    def test_authorization_request_errors(self):
        server = self.env["oauth.server"]
        check = server._check_authorization_request
        args = (self.client, common.REDIRECT_URI)
        cases = [
            ("unsupported_response_type", {"response_type": "token"}),
            ("invalid_request", {"code_challenge": None}),
            ("invalid_request", {"code_challenge_method": "plain"}),
            ("invalid_request", {"code_challenge_method": None}),
            ("invalid_request", {"code_challenge": "short"}),
            ("invalid_request", {"state": "x" * 3000}),
            ("invalid_target", {"resource": "https://other.example.com/api"}),
        ]
        for error, params in cases:
            with self.subTest(params=params):
                self.assertOAuthError(
                    error, check, *args, self.request_params(**params), self.user
                )
        self.resource.group_ids = self.env["res.groups"].create({"name": "API"})
        self.assertOAuthError(
            "access_denied", check, *args, self.request_params(), self.user
        )

    def test_approve_rechecks_access(self):
        server = self.env["oauth.server"]
        params = self.request_params()
        values = server._check_authorization_request(
            self.client, common.REDIRECT_URI, params, self.user
        )
        self.resource.group_ids = self.env["res.groups"].create({"name": "API"})
        self.assertOAuthError("access_denied", server._approve, values, self.user)
        self.client.active = False
        self.assertOAuthError("invalid_request", server._approve, values, self.user)

    # ------------------------------------------------------------------
    # Code exchange
    # ------------------------------------------------------------------

    def test_code_exchange(self):
        authorization, code, verifier = self.approve(scopes="read")
        tokens = self.exchange(code, verifier, resource=self.resource.uri + "/")
        self.assertEqual(
            set(tokens),
            {"access_token", "token_type", "expires_in", "scope", "refresh_token"},
        )
        self.assertEqual(tokens["token_type"], "Bearer")
        self.assertEqual(tokens["scope"], "read")
        self.assertEqual(tokens["expires_in"], 600)
        self.assertEqual(authorization.state, "active")
        header = jwt.get_unverified_header(tokens["access_token"])
        self.assertEqual(header["typ"], "at+jwt")
        payload = self.resource.jwt_validator_id._decode(tokens["access_token"])
        self.assertEqual(payload["iss"], common.ISSUER)
        self.assertEqual(payload["aud"], self.resource.uri)
        # recent PyJWT versions refuse non-string sub and jti claims
        self.assertEqual(payload["sub"], str(self.user.id))
        self.assertIsInstance(payload["jti"], str)
        self.assertEqual(payload["client_id"], self.client.identifier)
        self.assertEqual(payload["authorization_id"], authorization.id)
        self.assertEqual(self.check_token(tokens["access_token"]), self.user.id)

    def test_code_errors(self):
        _authorization, code, verifier = self.approve()
        cases = [
            ("invalid_grant", {"code": "unknown"}),
            ("invalid_grant", {"code": None}),
            ("invalid_grant", {"code_verifier": "x" * 43}),
            ("invalid_grant", {"code_verifier": None}),
            ("invalid_grant", {"redirect_uri": "http://127.0.0.1/callback"}),
            ("invalid_target", {"resource": "https://other.example.com/api"}),
        ]
        for error, params in cases:
            with self.subTest(params=params):
                params = dict({"code": code, "code_verifier": verifier}, **params)
                self.assertOAuthError(
                    error,
                    self.env["oauth.server.authorization"]._exchange_code,
                    self.client,
                    dict({"redirect_uri": common.REDIRECT_URI}, **params),
                )
        self.assertOAuthError(
            "invalid_grant",
            self.exchange,
            code,
            verifier,
            client=self.confidential_client,
        )
        # none of the failures consumed the code
        self.assertTrue(self.exchange(code, verifier)["access_token"])

    def test_code_expired(self):
        authorization, code, verifier = self.approve()
        authorization.code_expires_at = fields.Datetime.now() - timedelta(seconds=1)
        self.assertOAuthError("invalid_grant", self.exchange, code, verifier)

    def test_code_reuse_revokes(self):
        authorization, code, verifier = self.approve()
        tokens = self.exchange(code, verifier)
        self.assertOAuthErrorKeepingChanges(
            "invalid_grant", self.exchange, code, verifier
        )
        self.assertTrue(authorization.revoked)
        self.assertEqual(authorization.revoked_reason, "code_reuse")
        with self.assertRaises(UnauthorizedInvalidToken):
            self.check_token(tokens["access_token"])
        self.assertOAuthError("invalid_grant", self.refresh, tokens["refresh_token"])

    def test_code_after_user_loses_access(self):
        _authorization, code, verifier = self.approve()
        self.resource.group_ids = self.env["res.groups"].create({"name": "API"})
        self.assertOAuthError("invalid_grant", self.exchange, code, verifier)

    # ------------------------------------------------------------------
    # Refresh
    # ------------------------------------------------------------------

    def test_refresh_rotation(self):
        authorization, tokens = self.tokens()
        new_tokens = self.refresh(tokens["refresh_token"])
        self.assertNotEqual(new_tokens["refresh_token"], tokens["refresh_token"])
        self.assertEqual(self.check_token(new_tokens["access_token"]), self.user.id)
        self.assertTrue(authorization.last_refresh)
        # concurrent requests of one client may present the same token twice
        self.assertTrue(self.refresh(tokens["refresh_token"])["access_token"])
        self.assertFalse(authorization.revoked)

    def test_refresh_reuse_revokes(self):
        authorization, tokens = self.tokens()
        new_tokens = self.refresh(tokens["refresh_token"])
        old_token = self.env["oauth.server.refresh.token"]._get_by_token(
            tokens["refresh_token"]
        )
        old_token.used_at = fields.Datetime.now() - timedelta(minutes=5)
        self.assertOAuthErrorKeepingChanges(
            "invalid_grant", self.refresh, tokens["refresh_token"]
        )
        self.assertEqual(authorization.revoked_reason, "refresh_reuse")
        self.assertOAuthError(
            "invalid_grant", self.refresh, new_tokens["refresh_token"]
        )
        with self.assertRaises(UnauthorizedInvalidToken):
            self.check_token(new_tokens["access_token"])

    def test_refresh_errors(self):
        _authorization, tokens = self.tokens()
        refresh_token = tokens["refresh_token"]
        self.assertOAuthError("invalid_grant", self.refresh, "unknown")
        self.assertOAuthError(
            "invalid_grant",
            self.refresh,
            refresh_token,
            client=self.confidential_client,
        )
        self.assertOAuthError(
            "invalid_scope", self.refresh, refresh_token, scope="read admin"
        )
        self.assertOAuthError(
            "invalid_target", self.refresh, refresh_token, resource="https://x.com/a"
        )
        # refused requests do not use the token up
        self.assertTrue(self.refresh(refresh_token)["access_token"])

    def test_refresh_scope_narrowing(self):
        _authorization, tokens = self.tokens()
        tokens = self.refresh(tokens["refresh_token"], scope="read")
        self.assertEqual(tokens["scope"], "read")
        payload = self.resource.jwt_validator_id._decode(tokens["access_token"])
        self.assertEqual(payload["scope"], "read")

    def test_refresh_expired(self):
        _authorization, tokens = self.tokens()
        token = self.env["oauth.server.refresh.token"]._get_by_token(
            tokens["refresh_token"]
        )
        token.expires_at = fields.Datetime.now() - timedelta(seconds=1)
        self.assertOAuthError("invalid_grant", self.refresh, tokens["refresh_token"])

    def test_authorization_lifetime_caps_tokens(self):
        authorization, code, verifier = self.approve()
        authorization.expires_at = fields.Datetime.now() + timedelta(seconds=100)
        tokens = self.exchange(code, verifier)
        self.assertLessEqual(tokens["expires_in"], 100)
        token = self.env["oauth.server.refresh.token"]._get_by_token(
            tokens["refresh_token"]
        )
        self.assertLessEqual(token.expires_at, authorization.expires_at)
        authorization.expires_at = fields.Datetime.now() - timedelta(seconds=1)
        self.assertOAuthError("invalid_grant", self.refresh, tokens["refresh_token"])

    # ------------------------------------------------------------------
    # Access tokens presented to the resource
    # ------------------------------------------------------------------

    def test_access_token_checks(self):
        """Every change that withdraws access takes effect at once."""
        changes = [
            lambda a: a._revoke("admin"),
            lambda a: a.client_id.write({"active": False}),
            lambda a: a.resource_id.write({"active": False}),
            lambda a: a.user_id.write({"active": False}),
            lambda a: a.resource_id.write(
                {
                    "group_ids": [
                        (6, 0, self.env["res.groups"].create({"name": "G"}).ids)
                    ]
                }
            ),
            lambda a: a.write(
                {"expires_at": fields.Datetime.now() - timedelta(seconds=1)}
            ),
        ]
        for index, change in enumerate(changes):
            with self.subTest(change=index):
                user = new_test_user(self.env, login="oauth_change_%s" % index)
                client = self.client.copy({"name": "Copy %s" % index})
                authorization, tokens = self.tokens(client=client, user=user)
                self.assertEqual(self.check_token(tokens["access_token"]), user.id)
                change(authorization.sudo())
                with self.assertRaises(UnauthorizedInvalidToken):
                    self.check_token(tokens["access_token"])
                self.resource.write({"active": True, "group_ids": [(5,)]})

    def test_access_token_bound_to_resource(self):
        _authorization, tokens = self.tokens()
        other = self.env["oauth.server.resource"].create(
            {"name": "Other", "path": "/other_api", "scopes": "read write"}
        )
        with self.assertRaises(UnauthorizedInvalidToken):
            self.check_token(tokens["access_token"], resource=other)

    def test_forged_claims_refused(self):
        authorization, tokens = self.tokens()
        validator = self.resource.jwt_validator_id
        payload = validator._decode(tokens["access_token"])
        other_authorization, _tokens = self.tokens(user=self.other_user)
        for claims in (
            {"sub": str(self.other_user.id)},
            {"client_id": self.confidential_client.identifier},
            {"authorization_id": other_authorization.id},
            {"authorization_id": "x"},
        ):
            with self.subTest(claims=claims):
                forged = jwt.encode(
                    dict(payload, **claims), validator.secret_key, algorithm="HS256"
                )
                with self.assertRaises(UnauthorizedInvalidToken):
                    self.check_token(forged)
        self.assertEqual(authorization.state, "active")

    # ------------------------------------------------------------------
    # Revocation
    # ------------------------------------------------------------------

    def test_revoke_from_preferences(self):
        authorization, _tokens = self.tokens()
        self.assertIn(authorization, self.user.oauth_server_authorization_ids)
        with self.assertRaises(AccessError):
            authorization.with_user(self.other_user).action_revoke()
        authorization.with_user(self.user).action_revoke()
        self.assertEqual(authorization.revoked_reason, "user")
        self.user.invalidate_recordset(["oauth_server_authorization_ids"])
        self.assertNotIn(authorization, self.user.oauth_server_authorization_ids)
        self.assertFalse(authorization.refresh_token_ids)

    def test_users_see_only_their_authorizations(self):
        own, _tokens = self.tokens()
        other, _tokens = self.tokens(user=self.other_user)
        visible = self.env["oauth.server.authorization"].with_user(self.user).search([])
        self.assertIn(own, visible)
        self.assertNotIn(other, visible)

    def test_revoke_token(self):
        authorizations = self.env["oauth.server.authorization"]
        authorization, tokens = self.tokens()
        # tokens of another client are ignored
        authorizations._revoke_token(self.confidential_client, tokens["refresh_token"])
        self.assertFalse(authorization.revoked)
        authorizations._revoke_token(self.client, tokens["refresh_token"])
        self.assertEqual(authorization.revoked_reason, "client")
        authorization, tokens = self.tokens()
        authorizations._revoke_token(self.client, tokens["access_token"])
        self.assertTrue(authorization.revoked)
        # unknown tokens are ignored
        authorizations._revoke_token(self.client, "unknown")
        authorizations._revoke_token(self.client, None)

    # ------------------------------------------------------------------
    # Client authentication
    # ------------------------------------------------------------------

    def test_authenticate_client(self):
        authenticate = self.env["oauth.server"]._authenticate_client
        public, confidential = self.client, self.confidential_client
        self.assertEqual(authenticate(public.identifier, None), public)
        secret = self.client_secret
        self.assertEqual(authenticate(confidential.identifier, secret), confidential)
        self.assertEqual(
            authenticate(None, None, (confidential.identifier, secret)), confidential
        )
        for args in (
            (confidential.identifier, None),
            (confidential.identifier, "wrong"),
            (None, None, (confidential.identifier, "wrong")),
            ("unknown", None),
            (None, None),
        ):
            with self.subTest(args=args):
                error = self.assertOAuthError("invalid_client", authenticate, *args)
                self.assertEqual(error.status, 401)
        self.assertOAuthError(
            "invalid_request",
            authenticate,
            public.identifier,
            None,
            (confidential.identifier, secret),
        )

    def test_new_secret_replaces_old_one(self):
        authenticate = self.env["oauth.server"]._authenticate_client
        action = self.confidential_client.action_generate_secret()
        new_secret = action["context"]["default_secret"]
        self.assertOAuthError(
            "invalid_client",
            authenticate,
            self.confidential_client.identifier,
            self.client_secret,
        )
        self.assertEqual(
            authenticate(self.confidential_client.identifier, new_secret),
            self.confidential_client,
        )
