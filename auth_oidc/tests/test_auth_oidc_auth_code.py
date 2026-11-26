# Copyright 2021 ACSONE SA/NV <https://acsone.eu>
# License: AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

import contextlib
import json
import logging
from urllib.parse import parse_qs, urlparse

import responses
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from jose import jwt
from jose.exceptions import JWTError
from jose.utils import long_to_base64

import odoo
from odoo.exceptions import AccessDenied
from odoo.tests import common

from odoo.addons.http_routing.tests.common import MockRequest as _MockRequest

from ..controllers.main import OpenIDLogin

BASE_URL = f"http://localhost:{odoo.tools.config['http_port']}"


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
        (
            cls.rsa_key_pem,
            cls.rsa_key_public_pem,
            cls.rsa_key_public_jwk,
        ) = cls._generate_key()
        _, cls.second_key_public_pem, _ = cls._generate_key()

    @staticmethod
    def _generate_key():
        rsa_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=4096,
        )
        rsa_key_pem = rsa_key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.TraditionalOpenSSL,
            serialization.NoEncryption(),
        ).decode("utf8")
        rsa_key_public = rsa_key.public_key()
        rsa_key_public_pem = rsa_key_public.public_bytes(
            serialization.Encoding.PEM,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        ).decode("utf8")
        jwk = {
            # https://datatracker.ietf.org/doc/html/rfc7518#section-6.1
            "kty": "RSA",
            "use": "sig",
            "n": long_to_base64(rsa_key_public.public_numbers().n).decode("utf-8"),
            "e": long_to_base64(rsa_key_public.public_numbers().e).decode("utf-8"),
        }
        return rsa_key_pem, rsa_key_public_pem, jwk

    def setUp(self):
        super().setUp()
        # set up our test provider to bind the test user to it
        self.provider_rec = self.env["auth.oauth.provider"].create(
            {
                "name": "OAuth Provider for TestAuthOIDCAuthorizationCodeFlow",
                "client_id": "auth_oidc-test",
                "enabled": True,
                "body": "Config of an oauth provider for tests",
                "scope": "openid email",
                "flow": "id_token_code",
                "auth_endpoint": "http://localhost:8080/auth/realms/master/protocol/openid-connect/auth",
                "token_endpoint": "http://localhost:8080/auth/realms/master/protocol/openid-connect/token",
                "jwks_uri": "http://localhost:8080/auth/realms/master/protocol/openid-connect/certs",
            }
        )
        self.assertEqual(len(self.provider_rec), 1)

    def test_auth_link(self):
        """Test that the authentication link is correct."""
        # disable existing providers except our test provider
        self.env["auth.oauth.provider"].search(
            [("client_id", "!=", "auth_oidc-test")]
        ).write(dict(enabled=False))
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

    def _prepare_login_test_user(self):
        user = self.env["res.users"].create(
            {
                "login": "auth_oidc_test_user",
                "name": "Auth OIDC Test User",
            }
        )
        user.write({"oauth_provider_id": self.provider_rec.id, "oauth_uid": user.login})
        return user

    def _prepare_login_test_responses(
        self, access_token="42", id_token_body=None, id_token_headers=None, keys=None
    ):
        if id_token_body is None:
            id_token_body = {}
        if id_token_headers is None:
            id_token_headers = {"kid": "the_key_id"}
        responses.add(
            responses.POST,
            "http://localhost:8080/auth/realms/master/protocol/openid-connect/token",
            json={
                "access_token": access_token,
                "id_token": jwt.encode(
                    id_token_body,
                    self.rsa_key_pem,
                    algorithm="RS256",
                    headers=id_token_headers,
                ),
            },
        )
        if keys is None:
            if "kid" in id_token_headers:
                keys = [{"kid": "the_key_id", "keys": [self.rsa_key_public_pem]}]
            else:
                keys = [{"keys": [self.rsa_key_public_pem]}]
        responses.add(
            responses.GET,
            "http://localhost:8080/auth/realms/master/protocol/openid-connect/certs",
            json={"keys": keys},
        )

    @responses.activate
    def test_login(self):
        """Test that login works"""
        user = self._prepare_login_test_user()
        self._prepare_login_test_responses(id_token_body={"user_id": user.login})

        params = {"state": json.dumps({})}
        with MockRequest(self.env):
            db, login, token = self.env["res.users"].auth_oauth(
                self.provider_rec.id,
                params,
            )
        self.assertEqual(token, "42")
        self.assertEqual(login, user.login)

    @responses.activate
    def test_login_without_kid(self):
        """Test that login works when ID Token has no kid in header"""
        user = self._prepare_login_test_user()
        self._prepare_login_test_responses(
            id_token_body={"user_id": user.login},
            id_token_headers={},
            access_token=chr(42),
        )

        params = {"state": json.dumps({})}
        with MockRequest(self.env):
            db, login, token = self.env["res.users"].auth_oauth(
                self.provider_rec.id,
                params,
            )
        self.assertEqual(token, "*")
        self.assertEqual(login, user.login)

    @responses.activate
    def test_login_with_sub_claim(self):
        """Test that login works when ID Token contains only standard claims"""
        self.provider_rec.token_map = False
        user = self._prepare_login_test_user()
        self._prepare_login_test_responses(
            id_token_body={"sub": user.login}, access_token="1764"
        )

        params = {"state": json.dumps({})}
        with MockRequest(self.env):
            db, login, token = self.env["res.users"].auth_oauth(
                self.provider_rec.id,
                params,
            )
        self.assertEqual(token, "1764")
        self.assertEqual(login, user.login)

    @responses.activate
    def test_login_without_kid_multiple_keys_in_jwks(self):
        """
        Test that login fails if no kid is provided in ID Token and JWKS has multiple
        keys
        """
        user = self._prepare_login_test_user()
        self._prepare_login_test_responses(
            id_token_body={"user_id": user.login},
            id_token_headers={},
            access_token="6*7",
            keys=[
                {"kid": "other_key_id", "keys": [self.second_key_public_pem]},
                {"kid": "the_key_id", "keys": [self.rsa_key_public_pem]},
            ],
        )

        with self.assertRaises(
            JWTError,
            msg="OpenID Connect requires kid to be set if there is"
            " more than one key in the JWKS",
        ):
            with MockRequest(self.env):
                self.env["res.users"].auth_oauth(
                    self.provider_rec.id,
                    {"state": json.dumps({})},
                )

    @responses.activate
    def test_login_without_matching_key(self):
        """Test that login fails if no matching key can be found"""
        user = self._prepare_login_test_user()
        self._prepare_login_test_responses(
            id_token_body={"user_id": user.login},
            id_token_headers={},
            access_token="168/4",
            keys=[{"kid": "other_key_id", "keys": [self.second_key_public_pem]}],
        )

        with self.assertRaises(JWTError):
            with MockRequest(self.env):
                self.env["res.users"].auth_oauth(
                    self.provider_rec.id,
                    {"state": json.dumps({})},
                )

    @responses.activate
    def test_login_without_any_key(self):
        """Test that login fails if no key is provided by JWKS"""
        user = self._prepare_login_test_user()
        self._prepare_login_test_responses(
            id_token_body={"user_id": user.login},
            id_token_headers={},
            access_token="168/4",
            keys=[],
        )

        with self.assertRaises(AccessDenied):
            with MockRequest(self.env):
                with self.assertLogs(level=logging.ERROR) as logs:
                    self.env["res.users"].auth_oauth(
                        self.provider_rec.id,
                        {"state": json.dumps({})},
                    )
        self.assertEqual(len(logs.records), 1)
        self.assertEqual(logs.records[0].levelno, logging.ERROR)
        self.assertEqual(
            "ERROR:odoo.addons.auth_oidc.models.res_users:user_id claim not found in"
            " id_token (after mapping).",
            logs.output[0],
        )

    @responses.activate
    def test_login_with_multiple_keys_in_jwks(self):
        """Test that login works with multiple keys present in jwks"""
        user = self._prepare_login_test_user()
        self._prepare_login_test_responses(
            id_token_body={"user_id": user.login},
            access_token="2*3*7",
            keys=[
                {"kid": "other_key_id", "keys": [self.second_key_public_pem]},
                {"kid": "the_key_id", "keys": [self.rsa_key_public_pem]},
            ],
        )

        with MockRequest(self.env):
            db, login, token = self.env["res.users"].auth_oauth(
                self.provider_rec.id,
                {"state": json.dumps({})},
            )
        self.assertEqual(token, "2*3*7")
        self.assertEqual(login, user.login)

    @responses.activate
    def test_login_with_multiple_keys_in_jwks_same_kid(self):
        """Test that login works with multiple keys with the same kid present in jwks"""
        user = self._prepare_login_test_user()
        self._prepare_login_test_responses(
            id_token_body={"user_id": user.login},
            access_token="84/2",
            keys=[
                {"kid": "the_key_id", "keys": [self.second_key_public_pem]},
                {"kid": "the_key_id", "keys": [self.rsa_key_public_pem]},
            ],
        )

        with MockRequest(self.env):
            db, login, token = self.env["res.users"].auth_oauth(
                self.provider_rec.id,
                {"state": json.dumps({})},
            )
        self.assertEqual(token, "84/2")
        self.assertEqual(login, user.login)

    def test_code_verifier_rotates_between_requests(self):
        """Test that each request gets its own verifier

        Exercised on ``pkce.current_verifier`` directly: two requests reuse
        the same environment here, so the ORM would hand back a cached
        value from the first one and hide the rotation.
        """
        from .. import pkce

        with MockRequest(self.env):
            first = pkce.current_verifier(self.provider_rec.id)
        with MockRequest(self.env):
            second = pkce.current_verifier(self.provider_rec.id)
        self.assertTrue(first)
        self.assertNotEqual(first, second)

    def test_code_verifier_is_stable_within_a_request(self):
        """Test that listing providers twice in one request agrees

        The login page renders the auth links more than once per request.
        If the two renders disagreed, the challenge in the link the user
        clicks would not match the verifier filed for it.
        """
        self.env["auth.oauth.provider"].search(
            [("client_id", "!=", "auth_oidc-test")]
        ).write(dict(enabled=False))
        with MockRequest(self.env):
            first = OpenIDLogin().list_providers()[0]["auth_link"]
            second = OpenIDLogin().list_providers()[0]["auth_link"]
        self.assertEqual(
            parse_qs(urlparse(first).query)["code_challenge"],
            parse_qs(urlparse(second).query)["code_challenge"],
        )
        self.assertEqual(
            parse_qs(urlparse(first).query)["state"],
            parse_qs(urlparse(second).query)["state"],
        )

    def test_concurrent_authorizations_do_not_invalidate_each_other(self):
        """Test that two authorizations in one session each keep their verifier

        Two tabs, or a login page rendered again while an authorization is
        still in flight, must not overwrite each other -- that would make
        the first one fail with an invalid_grant at the provider.
        """
        from .. import pkce

        with MockRequest(self.env):
            state_a = pkce.remember("verifier-a", {"d": "db"})
            state_b = pkce.remember("verifier-b", {"d": "db"})
            self.assertNotEqual(state_a["k"], state_b["k"])
            self.assertEqual(pkce.claim(state_a), "verifier-a")
            self.assertEqual(pkce.claim(state_b), "verifier-b")
            # a verifier is good for exactly one token request
            self.assertEqual(pkce.claim(state_a), "")

    def test_code_verifier_not_stored_on_provider(self):
        """Test that the verifier is not a column of auth_oauth_provider"""
        field = self.env["auth.oauth.provider"]._fields["code_verifier"]
        self.assertFalse(field.store)
        self.assertEqual(field.compute, "_compute_code_verifier")

    @responses.activate
    def test_login_uses_verifier_from_state(self):
        """Test that the token request carries the verifier filed for this state"""
        user = self._prepare_login_test_user()
        self._prepare_login_test_responses(id_token_body={"user_id": user.login})
        self.env["auth.oauth.provider"].search(
            [("client_id", "!=", "auth_oidc-test")]
        ).write(dict(enabled=False))

        with MockRequest(self.env):
            auth_link = OpenIDLogin().list_providers()[0]["auth_link"]
            state = parse_qs(urlparse(auth_link).query)["state"][0]
            self.env["res.users"].auth_oauth(
                self.provider_rec.id,
                {"state": state, "code": "the_code"},
            )

        token_request = [
            call.request.body
            for call in responses.calls
            if call.request.url.endswith("/token")
        ]
        self.assertTrue(token_request)
        body = parse_qs(token_request[0])
        self.assertIn("code_verifier", body)
        self.assertTrue(body["code_verifier"][0])

    @responses.activate
    def test_login_without_state_verifier_sends_empty(self):
        """Test that a callback without a filed verifier does not crash

        An authorization started before the upgrade has no session entry.
        The token exchange is then rejected by the provider, but it must
        not raise here.
        """
        user = self._prepare_login_test_user()
        self._prepare_login_test_responses(id_token_body={"user_id": user.login})

        with MockRequest(self.env):
            self.env["res.users"].auth_oauth(
                self.provider_rec.id,
                {"state": json.dumps({}), "code": "the_code"},
            )

        token_request = [
            call.request.body
            for call in responses.calls
            if call.request.url.endswith("/token")
        ]
        self.assertTrue(token_request)
        # present but empty: the provider rejects the exchange, which is the
        # controlled failure we want, rather than the request raising here
        self.assertEqual(parse_qs(token_request[0])["code_verifier"], [""])

    @responses.activate
    def test_login_with_jwk_format(self):
        """Test that login works with proper jwks format"""
        user = self._prepare_login_test_user()
        self.rsa_key_public_jwk["kid"] = "the_key_id"
        self._prepare_login_test_responses(
            id_token_body={"user_id": user.login},
            keys=[self.rsa_key_public_jwk],
            access_token="122/3",
        )

        with MockRequest(self.env):
            db, login, token = self.env["res.users"].auth_oauth(
                self.provider_rec.id,
                {"state": json.dumps({})},
            )
        self.assertEqual(token, "122/3")
        self.assertEqual(login, user.login)
