# Copyright 2026 Lorenzo Battistini
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
"""Fixtures shared by the tests.

Import this module rather than its names: Odoo collects every test class
found in a test module's namespace.
"""

import secrets

from odoo.tests.common import new_test_user

from ..utils import pkce_s256

ISSUER = "https://erp.example.com"
REDIRECT_URI = "https://app.example.com/callback"
LOOPBACK_REDIRECT_URI = "http://127.0.0.1/callback"


def pkce_pair():
    verifier = secrets.token_urlsafe(48)
    return verifier, pkce_s256(verifier)


def _remove_attrs(cls, names):
    for name in names & set(vars(cls)):
        delattr(cls, name)


class AuthMethodsMixin:
    """For the test cases that create protected resources.

    auth_jwt adds the ``auth="jwt_<name>"`` methods of each validator, those of
    the resources included, to the ir.http class, where they outlive the
    records rolled back after a test; Odoo fails the tests that leave such
    attributes behind. The methods a test adds are removed after it; call
    ``accept_auth_methods()`` at the end of setUpClass to keep those of the
    class fixtures until the end of the class.
    """

    @classmethod
    def accept_auth_methods(cls):
        ir_http = type(cls.env["ir.http"])
        added = set(vars(ir_http)) - cls.attrs_before["ir.http"]
        cls.attrs_before["ir.http"] |= added
        cls.addClassCleanup(_remove_attrs, ir_http, added)

    def setUp(self):
        super().setUp()
        ir_http = type(self.env["ir.http"])
        attrs_before = set(vars(ir_http))
        self.addCleanup(
            lambda: _remove_attrs(ir_http, set(vars(ir_http)) - attrs_before)
        )


class OAuthServerMixin(AuthMethodsMixin):
    """A resource, a public and a confidential client, and a user."""

    @classmethod
    def setup_oauth_server(cls):
        env = cls.env
        env["ir.config_parameter"].sudo().set_param("auth_oauth_server.issuer", ISSUER)
        cls.resource = env["oauth.server.resource"].create(
            {"name": "Test API", "path": "/test_api", "scopes": "read write"}
        )
        cls.client = env["oauth.server.client"].create(
            {
                "name": "Test App",
                "redirect_uris": f"{REDIRECT_URI}\n{LOOPBACK_REDIRECT_URI}",
            }
        )
        cls.confidential_client = env["oauth.server.client"].create(
            {"name": "Test Server App", "redirect_uris": REDIRECT_URI}
        )
        action = cls.confidential_client.action_generate_secret()
        cls.client_secret = action["context"]["default_secret"]
        cls.user = new_test_user(env, login="oauth_user")
        cls.other_user = new_test_user(env, login="oauth_other")
        cls.accept_auth_methods()

    def approve(self, client=None, user=None, scopes="read write"):
        """What the consent page does: returns (authorization, code, verifier)."""
        verifier, challenge = pkce_pair()
        authorization, code = self.env[
            "oauth.server.authorization"
        ]._create_from_consent(
            user or self.user,
            client or self.client,
            self.resource,
            scopes,
            REDIRECT_URI,
            challenge,
        )
        return authorization, code, verifier

    def exchange(self, code, verifier, client=None, **params):
        params = dict(
            {"code": code, "code_verifier": verifier, "redirect_uri": REDIRECT_URI},
            **params,
        )
        return self.env["oauth.server.authorization"]._exchange_code(
            client or self.client, params
        )

    def refresh(self, refresh_token, client=None, **params):
        params = dict({"refresh_token": refresh_token}, **params)
        return self.env["oauth.server.authorization"]._refresh(
            client or self.client, params
        )

    def tokens(self, client=None, user=None):
        """Approve and exchange the code: returns (authorization, tokens)."""
        authorization, code, verifier = self.approve(client=client, user=user)
        return authorization, self.exchange(code, verifier, client=client)

    def check_token(self, access_token, resource=None):
        """The uid an access token runs as on ``resource``."""
        validator = (resource or self.resource).jwt_validator_id
        payload = validator._decode(access_token)
        return validator._get_and_check_uid(payload)
