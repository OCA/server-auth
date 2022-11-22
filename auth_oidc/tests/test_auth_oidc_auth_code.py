# Copyright 2021 ACSONE SA/NV <https://acsone.eu>
# License: AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

import contextlib
import json
import responses
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from urllib.parse import parse_qs, urlparse
from jose import jwt

import odoo
from odoo.tests import common

from odoo.addons.auth_oidc.controllers.main import OpenIDLogin
from odoo.addons.website.tools import MockRequest as _MockRequest

BASE_URL = "http://localhost:%s" % odoo.tools.config["http_port"]


@contextlib.contextmanager
def MockRequest(env):
    with _MockRequest(env) as request:
        request.httprequest.url_root = BASE_URL + "/"
        request.params = {}
        yield request


class TestAuthOIDCAuthorizationCodeFlow(common.HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.rsa_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=4096,
        )
        cls.rsa_key_pem = cls.rsa_key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.TraditionalOpenSSL,
            serialization.NoEncryption(),
        ).decode("utf8")
        cls.rsa_key_public = cls.rsa_key.public_key()
        cls.rsa_key_public_pem = cls.rsa_key_public.public_bytes(
            serialization.Encoding.PEM,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        ).decode("utf8")

    def setUp(self):
        super().setUp()
        # search our test provider and bind the demo user to it
        self.provider_rec = self.env["auth.oauth.provider"].search(
            [("client_id", "=", "auth_oidc-test")]
        )
        self.assertEqual(len(self.provider_rec), 1)
        # disable existing providers except our test provider
        self.env["auth.oauth.provider"].search(
            [("client_id", "!=", "auth_oidc-test")]
        ).write(dict(enabled=False))

    def test_auth_link(self):
        """Test that the authentication link is correct."""
        with MockRequest(self.env):
            providers = OpenIDLogin().list_providers()
            self.assertEqual(len(providers), 1)
            auth_link = providers[0]["auth_link"]
            assert auth_link.startswith(self.provider_rec.auth_endpoint)
            params = parse_qs(urlparse(auth_link).query)
            self.assertEqual(params["response_type"], ["code"])
            self.assertEqual(params["client_id"], [self.provider_rec.client_id])
            self.assertEqual(params["scope"], ["openid email"])
            self.assertTrue(params["code_challenge"])
            self.assertEqual(params["code_challenge_method"], ["S256"])
            self.assertTrue(params["nonce"])
            self.assertTrue(params["state"])
            self.assertEqual(params["redirect_uri"], [BASE_URL + "/auth_oauth/signin"])

    def test_group_expression(self):
        """Test that group expressions evaluate correctly"""
        group_line = self.env.ref('auth_oidc.local_keycloak').group_line_ids[:1]
        group_line.expression = 'token["test"]["test"] == 1'
        self.assertFalse(group_line._eval_expression(self.env.user, {}))

    @responses.activate
    def test_login(self):
        """Test that login works"""
        user = self.env.ref("base.user_demo")
        user.write({
            'oauth_provider_id': self.provider_rec.id,
            'oauth_uid': user.login,
        })
        responses.add(
            responses.POST,
            "http://localhost:8080/auth/realms/master/protocol/openid-connect/token",
            json={
                "access_token": "42",
                "id_token": jwt.encode(
                    {"user_id": user.login},
                    self.rsa_key_pem, algorithm="RS256",
                    headers={"kid": "the_key_id"},
                ),
            },
        )
        responses.add(
            responses.GET,
            "http://localhost:8080/auth/realms/master/protocol/openid-connect/certs",
            json={
                "keys": [{
                    "kid": "the_key_id",
                    "keys": [self.rsa_key_public_pem],
                }],
            },
        )
        params = {"state": json.dumps({})}
        with MockRequest(self.env):
            db, login, token = self.env["res.users"].auth_oauth(
                self.provider_rec.id, params,
            )
        self.assertEqual(token, "42")
        self.assertEqual(login, user.login)
