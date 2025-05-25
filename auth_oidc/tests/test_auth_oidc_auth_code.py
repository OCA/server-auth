# Copyright 2021 ACSONE SA/NV <https://acsone.eu>
# License: AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

import contextlib
import json
import logging
from urllib.parse import parse_qs, urlparse

import responses
import secrets
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa, ec
from jose import jwt
from jose.exceptions import JWTError
from jose.utils import long_to_base64, base64url_encode

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
        ) = cls._generate_rsa_key()
        _, cls.second_key_public_pem, _ = cls._generate_rsa_key()
        
        (
            cls.es256_key_pem,
            cls.es256_key_public_pem,
            cls.es256_key_public_jwk,
        ) = cls._generate_ec_key(curve=ec.SECP256R1())
        
        (
            cls.es384_key_pem,
            cls.es384_key_public_pem,
            cls.es384_key_public_jwk,
        ) = cls._generate_ec_key(curve=ec.SECP384R1())
        
        cls.hs256_key = secrets.token_bytes(32)
        cls.hs256_jwk = {
            "kty": "oct",
            "use": "sig",
            "alg": "HS256",
            "kid": "hs256-key",
            "k": base64url_encode(cls.hs256_key).decode("utf-8"),
        }

    @staticmethod
    def _generate_rsa_key():
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
        
    @staticmethod
    def _generate_ec_key(curve):
        ec_key = ec.generate_private_key(curve)
        ec_key_pem = ec_key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.TraditionalOpenSSL,
            serialization.NoEncryption(),
        ).decode("utf8")
        ec_key_public = ec_key.public_key()
        ec_key_public_pem = ec_key_public.public_bytes(
            serialization.Encoding.PEM,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        ).decode("utf8")
        
        curve_name = "P-256" if isinstance(curve, ec.SECP256R1) else "P-384"
        alg = "ES256" if isinstance(curve, ec.SECP256R1) else "ES384"
        
        public_numbers = ec_key_public.public_numbers()
        x = long_to_base64(public_numbers.x).decode("utf-8")
        y = long_to_base64(public_numbers.y).decode("utf-8")
        
        jwk = {
            "kty": "EC",
            "use": "sig",
            "crv": curve_name,
            "alg": alg,
            "x": x,
            "y": y,
            "kid": "ec-key-" + alg.lower(),
        }
        return ec_key_pem, ec_key_public_pem, jwk

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
        self, access_token="42", id_token_body=None, id_token_headers=None, keys=None,
        algorithm="RS256", private_key=None, public_key=None
    ):
        if id_token_body is None:
            id_token_body = {}
        if id_token_headers is None:
            id_token_headers = {"kid": "the_key_id"}
            
        if private_key is None:
            if algorithm == "RS256":
                private_key = self.rsa_key_pem
                public_key_pem = self.rsa_key_public_pem
            elif algorithm == "ES256":
                private_key = self.es256_key_pem
                public_key_pem = self.es256_key_public_pem
            elif algorithm == "ES384":
                private_key = self.es384_key_pem
                public_key_pem = self.es384_key_public_pem
            elif algorithm == "HS256":
                private_key = self.hs256_key
                # For HS256, we don't use public_key_pem as it's a symmetric key
                public_key_pem = None
        else:
            # For asymmetric algorithms, public_key_pem is needed
            public_key_pem = public_key or private_key
            
        responses.add(
            responses.POST,
            "http://localhost:8080/auth/realms/master/protocol/openid-connect/token",
            json={
                "access_token": access_token,
                "id_token": jwt.encode(
                    id_token_body,
                    private_key,
                    algorithm=algorithm,
                    headers=id_token_headers,
                ),
            },
        )
        
        # Handle the keys parameter based on the algorithm
        if keys is None:
            if algorithm == "HS256":
                # For HS256, we use the JWK directly
                keys = [self.hs256_jwk]
            elif algorithm == "ES256":
                # For ES256, we use the JWK directly
                keys = [self.es256_key_public_jwk]
            elif algorithm == "ES384":
                # For ES384, we use the JWK directly
                keys = [self.es384_key_public_jwk]
            else:
                # For RS256, we use the traditional approach
                if "kid" in id_token_headers:
                    keys = [{"kid": id_token_headers["kid"], "keys": [public_key_pem]}]
                else:
                    keys = [{"keys": [public_key_pem]}]
                
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
        
    @responses.activate
    def test_login_with_es256_algorithm(self):
        """Test that login works with ES256 algorithm"""
        user = self._prepare_login_test_user()
        
        self._prepare_login_test_responses(
            id_token_body={"user_id": user.login},
            id_token_headers={"kid": self.es256_key_public_jwk["kid"]},
            algorithm="ES256",
            access_token="es256token",
            keys=[self.es256_key_public_jwk],
        )
        
        with MockRequest(self.env):
            db, login, token = self.env["res.users"].auth_oauth(
                self.provider_rec.id,
                {"state": json.dumps({})},
            )
        self.assertEqual(token, "es256token")
        self.assertEqual(login, user.login)
        
    @responses.activate
    def test_login_with_es384_algorithm(self):
        """Test that login works with ES384 algorithm"""
        user = self._prepare_login_test_user()
        
        self._prepare_login_test_responses(
            id_token_body={"user_id": user.login},
            id_token_headers={"kid": self.es384_key_public_jwk["kid"]},
            algorithm="ES384",
            access_token="es384token",
            keys=[self.es384_key_public_jwk],
        )
        
        with MockRequest(self.env):
            db, login, token = self.env["res.users"].auth_oauth(
                self.provider_rec.id,
                {"state": json.dumps({})},
            )
        self.assertEqual(token, "es384token")
        self.assertEqual(login, user.login)
        
    @responses.activate
    def test_login_with_hs256_algorithm(self):
        """Test that login works with HS256 algorithm"""
        user = self._prepare_login_test_user()
        
        self._prepare_login_test_responses(
            id_token_body={"user_id": user.login},
            id_token_headers={"kid": self.hs256_jwk["kid"]},
            algorithm="HS256",
            access_token="hs256token",
            keys=[self.hs256_jwk],
        )
        
        with MockRequest(self.env):
            db, login, token = self.env["res.users"].auth_oauth(
                self.provider_rec.id,
                {"state": json.dumps({})},
            )
        self.assertEqual(token, "hs256token")
        self.assertEqual(login, user.login)
