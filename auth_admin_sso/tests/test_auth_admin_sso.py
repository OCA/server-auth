# Copyright 2026 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import contextlib
import os
import re
from unittest import mock
from urllib.parse import parse_qs, urlparse

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from jose import jwt
from jose.utils import long_to_base64

from odoo import http
from odoo.tests import HttpCase, tagged

from ..controllers import main

CLIENT = "the-client"
ROLE = "odoo-test"
ISSUER = "https://idp.example.com/the-tenant/v2.0"
DISCOVERY_URL = ISSUER + "/.well-known/openid-configuration"
DISCOVERY = {
    "issuer": ISSUER,
    "authorization_endpoint": "https://idp.example.com/authorize",
    "token_endpoint": "https://idp.example.com/token",
    "jwks_uri": "https://idp.example.com/keys",
}
ENV = {
    # Trailing "/" must be stripped.
    "AUTH_ADMIN_SSO_ISSUER": ISSUER + "/",
    "AUTH_ADMIN_SSO_CLIENT_ID": CLIENT,
    "AUTH_ADMIN_SSO_REQUIRED_ROLE": ROLE,
}


@tagged("post_install", "-at_install")
class TestAuthAdminSSO(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        cls.private_pem = key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.TraditionalOpenSSL,
            serialization.NoEncryption(),
        ).decode()
        numbers = key.public_key().public_numbers()
        cls.jwk = {
            "kty": "RSA",
            "use": "sig",
            "kid": "the-kid",
            "n": long_to_base64(numbers.n).decode(),
            "e": long_to_base64(numbers.e).decode(),
        }

    def setUp(self):
        super().setUp()
        main._jwks_cache.clear()
        main._discovery_cache.clear()
        env_patcher = mock.patch.dict(os.environ, ENV)
        env_patcher.start()
        self.addCleanup(env_patcher.stop)
        get_patcher = mock.patch.object(main.requests, "get", side_effect=self._get)
        self.requests_get = get_patcher.start()
        self.addCleanup(get_patcher.stop)

    def _get(self, url, timeout=None):
        payloads = {
            DISCOVERY_URL: DISCOVERY,
            DISCOVERY["jwks_uri"]: {"keys": [self.jwk]},
        }
        response = mock.Mock()
        response.json.return_value = payloads[url]
        return response

    def _start(self):
        response = self.url_open("/auth_admin_sso/login", allow_redirects=False)
        self.assertEqual(response.status_code, 303)
        return parse_qs(urlparse(response.headers["Location"]).query)

    def _claims(self, nonce, **overrides):
        claims = {
            "iss": ISSUER,
            "aud": CLIENT,
            "exp": 9999999999,
            "iat": 1,
            "nonce": nonce,
            "email": "john.doe@example.com",
            "roles": [ROLE],
        }
        claims.update(overrides)
        return claims

    def _callback(self, state, claims, expect_warning=False):
        """Call the callback; with ``expect_warning``, capture its warnings."""
        id_token = jwt.encode(
            claims, self.private_pem, algorithm="RS256", headers={"kid": "the-kid"}
        )
        token_response = mock.Mock(ok=True)
        token_response.json.return_value = {"id_token": id_token}
        logs = (
            self.assertLogs(main.__name__, "WARNING")
            if expect_warning
            else contextlib.nullcontext()
        )
        with (
            mock.patch.object(
                main.requests, "post", return_value=token_response
            ) as post,
            logs,
        ):
            response = self.url_open(
                f"/auth_admin_sso/callback?code=the-code&state={state}",
                allow_redirects=False,
            )
        return response, post

    def _session_uid(self):
        sid = self.opener.cookies["session_id"]
        return http.root.session_store.get(sid).uid

    def test_not_configured(self):
        with mock.patch.dict(os.environ, {"AUTH_ADMIN_SSO_CLIENT_ID": ""}):
            response = self.url_open("/auth_admin_sso/login", allow_redirects=False)
        self.assertEqual(response.status_code, 404)

    def test_start(self):
        response = self.url_open("/auth_admin_sso/login", allow_redirects=False)
        location = urlparse(response.headers["Location"])
        self.assertEqual(
            f"{location.scheme}://{location.netloc}{location.path}",
            DISCOVERY["authorization_endpoint"],
        )
        params = parse_qs(location.query)
        self.assertEqual(params["client_id"], [CLIENT])
        self.assertEqual(params["response_type"], ["code"])
        self.assertEqual(params["code_challenge_method"], ["S256"])
        self.assertTrue(params["code_challenge"])
        self.assertTrue(params["state"])
        self.assertTrue(params["nonce"])
        self.assertTrue(params["redirect_uri"][0].endswith("/auth_admin_sso/callback"))

    def test_login(self):
        params = self._start()
        response, post = self._callback(
            params["state"][0], self._claims(params["nonce"][0])
        )
        self.assertEqual(response.status_code, 303)
        self.assertEqual(post.call_args.args[0], DISCOVERY["token_endpoint"])
        self.assertNotIn("client_secret", post.call_args.kwargs["data"])
        self.assertTrue(post.call_args.kwargs["data"]["code_verifier"])
        self.assertEqual(self._session_uid(), self.env.ref("base.user_admin").id)

    def _login_with_roles(self, roles, expect_warning=False):
        params = self._start()
        claims = self._claims(params["nonce"][0], roles=roles)
        response, _post = self._callback(
            params["state"][0], claims, expect_warning=expect_warning
        )
        return response

    def _create_user(self, login):
        return self.env["res.users"].create({"name": login, "login": login})

    def test_default_login_override(self):
        user = self._create_user("shared")
        with mock.patch.dict(os.environ, {"AUTH_ADMIN_SSO_DEFAULT_LOGIN": "shared"}):
            response = self._login_with_roles([ROLE])
        self.assertEqual(response.status_code, 303)
        self.assertEqual(self._session_uid(), user.id)

    def test_username_role_wins(self):
        user = self._create_user("john")
        response = self._login_with_roles([ROLE, f"{ROLE}.username.john"])
        self.assertEqual(response.status_code, 303)
        self.assertEqual(self._session_uid(), user.id)

    def test_username_role_alone(self):
        user = self._create_user("john")
        response = self._login_with_roles([f"{ROLE}.username.john"])
        self.assertEqual(response.status_code, 303)
        self.assertEqual(self._session_uid(), user.id)

    def test_two_username_roles(self):
        self._create_user("john")
        self._create_user("jane")
        response = self._login_with_roles(
            [ROLE, f"{ROLE}.username.john", f"{ROLE}.username.jane"],
            expect_warning=True,
        )
        self._assert_refused(response)

    def test_two_username_roles_with_default_login(self):
        self._create_user("john")
        response = self._login_with_roles(
            [f"{ROLE}.username.john", f"{ROLE}.username.admin"],
            expect_warning=True,
        )
        self.assertEqual(response.status_code, 303)
        self.assertEqual(self._session_uid(), self.env.ref("base.user_admin").id)

    def test_username_role_unknown_user(self):
        response = self._login_with_roles(
            [ROLE, f"{ROLE}.username.nobody"], expect_warning=True
        )
        self._assert_refused(response)

    def test_unknown_keyword_ignored(self):
        response = self._login_with_roles([ROLE, f"{ROLE}.foo.john"])
        self.assertEqual(response.status_code, 303)
        self.assertEqual(self._session_uid(), self.env.ref("base.user_admin").id)

    def test_unknown_keyword_alone(self):
        self._assert_refused(
            self._login_with_roles([f"{ROLE}.foo.john"], expect_warning=True)
        )

    def test_empty_username_ignored(self):
        self._assert_refused(
            self._login_with_roles([f"{ROLE}.username."], expect_warning=True)
        )

    def _assert_refused(self, response):
        self.assertEqual(response.status_code, 403)
        self.assertRegex(response.text, r"^Login refused\. Reference: [0-9a-f-]{36}$")
        self.assertFalse(self._session_uid())

    def _assert_issue(self, response):
        self.assertEqual(response.status_code, 500)
        self.assertIn("issue with the Admin SSO login", response.text)
        self.assertRegex(response.text, r"reference [0-9a-f-]{36}\.")
        self.assertNotIn("jose", response.text)
        self.assertFalse(self._session_uid())

    def test_jose_missing_start(self):
        with (
            mock.patch.object(main, "jwt", None),
            self.assertLogs(main.__name__, "WARNING") as logs,
        ):
            response = self.url_open("/auth_admin_sso/login", allow_redirects=False)
        self._assert_issue(response)
        ref = re.search(r"[0-9a-f-]{36}", response.text).group()
        self.assertIn(ref, logs.output[0])
        self.assertIn("python-jose not installed", logs.output[0])

    def test_unexpected_error(self):
        params = self._start()
        with (
            mock.patch.object(
                main.AdminSSO,
                "_auth_admin_sso_login_as",
                side_effect=RuntimeError("boom"),
            ),
            self.assertLogs(main.__name__, "WARNING") as logs,
        ):
            response, _post = self._callback(
                params["state"][0], self._claims(params["nonce"][0])
            )
        self._assert_issue(response)
        self.assertNotIn("boom", response.text)
        self.assertIn("boom", logs.output[0])

    def test_token_endpoint_unreachable(self):
        params = self._start()
        with (
            mock.patch.object(
                main.requests,
                "post",
                side_effect=main.requests.ConnectionError("down"),
            ),
            # Captured: the OCB CI fails on any traceback left in the log.
            self.assertLogs(main.__name__, "WARNING") as logs,
        ):
            response = self.url_open(
                f"/auth_admin_sso/callback?code=c&state={params['state'][0]}",
                allow_redirects=False,
            )
        self._assert_issue(response)
        self.assertIn("down", logs.output[0])

    def test_discovery_unreachable(self):
        self.requests_get.side_effect = main.requests.ConnectionError("down")
        with self.assertLogs(main.__name__, "WARNING") as logs:
            response = self.url_open("/auth_admin_sso/login", allow_redirects=False)
        self._assert_issue(response)
        ref = re.search(r"[0-9a-f-]{36}", response.text).group()
        self.assertIn(ref, logs.output[0])
        self.assertIn("down", logs.output[0])

    def test_custom_roles_claim(self):
        with mock.patch.dict(os.environ, {"AUTH_ADMIN_SSO_ROLES_CLAIM": "groups"}):
            params = self._start()
            claims = self._claims(params["nonce"][0], roles=[], groups=ROLE)
            response, _post = self._callback(params["state"][0], claims)
        self.assertEqual(response.status_code, 303)
        self.assertEqual(self._session_uid(), self.env.ref("base.user_admin").id)

    def test_custom_roles_claim_ignores_roles(self):
        with mock.patch.dict(os.environ, {"AUTH_ADMIN_SSO_ROLES_CLAIM": "groups"}):
            params = self._start()
            response, _post = self._callback(
                params["state"][0],
                self._claims(params["nonce"][0]),
                expect_warning=True,
            )
        self._assert_refused(response)

    def test_unknown_provider(self):
        with mock.patch.dict(os.environ, {"AUTH_ADMIN_SSO_PROVIDER": "nope"}):
            with self.assertLogs(main.__name__, "WARNING") as logs:
                response = self.url_open("/auth_admin_sso/login", allow_redirects=False)
        self._assert_issue(response)
        self.assertIn("unknown provider 'nope'", logs.output[0])

    def test_extension_provider(self):
        """An add-on inheriting AdminSSO adds a provider (here: "dummy")."""
        AdminSSO = main.AdminSSO
        originals = {
            name: getattr(AdminSSO, name)
            for name in (
                "_auth_admin_sso_authorization_url",
                "_auth_admin_sso_fetch_claims",
                "_auth_admin_sso_check_nonce",
                "_auth_admin_sso_get_roles",
            )
        }

        def authorization_url(self, settings, redirect_uri, state, nonce, challenge):
            if settings["provider"] != "dummy":
                return originals["_auth_admin_sso_authorization_url"](
                    self, settings, redirect_uri, state, nonce, challenge
                )
            return f"https://dummy.example.com/auth?state={state}"

        def fetch_claims(self, settings, code, code_verifier, redirect_uri):
            if settings["provider"] != "dummy":
                return originals["_auth_admin_sso_fetch_claims"](
                    self, settings, code, code_verifier, redirect_uri
                )
            if code != "good":
                raise main.SSOError("bad code")
            return {"email": "jane@example.com", "teams": [ROLE]}

        def check_nonce(self, settings, claims, nonce):
            if settings["provider"] != "dummy":
                return originals["_auth_admin_sso_check_nonce"](
                    self, settings, claims, nonce
                )

        def get_roles(self, settings, claims):
            if settings["provider"] != "dummy":
                return originals["_auth_admin_sso_get_roles"](self, settings, claims)
            return claims["teams"]

        overrides = {
            "_auth_admin_sso_authorization_url": authorization_url,
            "_auth_admin_sso_fetch_claims": fetch_claims,
            "_auth_admin_sso_check_nonce": check_nonce,
            "_auth_admin_sso_get_roles": get_roles,
        }
        env = {
            "AUTH_ADMIN_SSO_PROVIDER": "dummy",
            # The dummy provider does not need the OIDC settings.
            "AUTH_ADMIN_SSO_ISSUER": "",
            "AUTH_ADMIN_SSO_CLIENT_ID": "",
        }
        with (
            mock.patch.multiple(AdminSSO, **overrides),
            mock.patch.dict(os.environ, env),
        ):
            response = self.url_open("/auth_admin_sso/login", allow_redirects=False)
            location = response.headers["Location"]
            self.assertTrue(location.startswith("https://dummy.example.com/auth"))
            state = parse_qs(urlparse(location).query)["state"][0]
            response = self.url_open(
                f"/auth_admin_sso/callback?code=good&state={state}",
                allow_redirects=False,
            )
        self.assertEqual(response.status_code, 303)
        self.assertEqual(self._session_uid(), self.env.ref("base.user_admin").id)
        self.requests_get.assert_not_called()

    def test_wrong_state(self):
        params = self._start()
        response, _post = self._callback(
            "wrong", self._claims(params["nonce"][0]), expect_warning=True
        )
        self._assert_refused(response)

    def test_wrong_nonce(self):
        params = self._start()
        response, _post = self._callback(
            params["state"][0], self._claims("wrong"), expect_warning=True
        )
        self._assert_refused(response)

    def test_missing_role(self):
        params = self._start()
        claims = self._claims(params["nonce"][0], roles=["odoo-other"])
        response, _post = self._callback(
            params["state"][0], claims, expect_warning=True
        )
        self._assert_refused(response)

    def test_wrong_audience(self):
        params = self._start()
        claims = self._claims(params["nonce"][0], aud="other-client")
        response, _post = self._callback(
            params["state"][0], claims, expect_warning=True
        )
        self._assert_refused(response)

    def test_wrong_issuer(self):
        params = self._start()
        claims = self._claims(
            params["nonce"][0], iss="https://idp.example.com/other/v2.0"
        )
        response, _post = self._callback(
            params["state"][0], claims, expect_warning=True
        )
        self._assert_refused(response)

    def _post_login(self, login, password="sso"):
        page = self.url_open("/web/login")
        csrf = re.search(r'name="csrf_token" value="([^"]+)"', page.text).group(1)
        return self.url_open(
            "/web/login",
            data={"login": login, "password": password, "csrf_token": csrf},
            allow_redirects=False,
        )

    def _assert_redirects_to_sso(self, response):
        self.assertEqual(response.status_code, 303)
        self.assertEqual(
            urlparse(response.headers["Location"]).path, "/auth_admin_sso/login"
        )

    def _assert_normal_login(self, response):
        # Wrong password: Odoo renders the login form again, with an error.
        self.assertEqual(response.status_code, 200)
        self.assertIn("Wrong login/password", response.text)

    def test_redirect_login_enabled(self):
        with mock.patch.dict(os.environ, {"AUTH_ADMIN_SSO_REDIRECT_LOGIN": "True"}):
            self._assert_redirects_to_sso(self._post_login("admin"))

    def test_redirect_login_case_sensitive(self):
        with mock.patch.dict(os.environ, {"AUTH_ADMIN_SSO_REDIRECT_LOGIN": "1"}):
            self._assert_normal_login(self._post_login("Admin"))

    def test_redirect_login_stripped(self):
        with mock.patch.dict(os.environ, {"AUTH_ADMIN_SSO_REDIRECT_LOGIN": "1"}):
            self._assert_redirects_to_sso(self._post_login(" admin "))

    def test_redirect_login_case_insensitive(self):
        env = {
            "AUTH_ADMIN_SSO_REDIRECT_LOGIN": "1",
            "AUTH_ADMIN_SSO_CASE_INSENSITIVE_LOGIN": " True ",
        }
        with mock.patch.dict(os.environ, env):
            self._assert_redirects_to_sso(self._post_login("Admin"))

    def test_redirect_login_case_insensitive_invalid_value(self):
        env = {
            "AUTH_ADMIN_SSO_REDIRECT_LOGIN": "1",
            "AUTH_ADMIN_SSO_CASE_INSENSITIVE_LOGIN": "foo",
        }
        with mock.patch.dict(os.environ, env):
            self._assert_normal_login(self._post_login("Admin"))

    def test_redirect_login_other_password(self):
        with mock.patch.dict(os.environ, {"AUTH_ADMIN_SSO_REDIRECT_LOGIN": "1"}):
            self._assert_normal_login(self._post_login("admin", "wrong"))

    def test_redirect_login_custom_keyword(self):
        with mock.patch.dict(
            os.environ,
            {
                "AUTH_ADMIN_SSO_REDIRECT_LOGIN": "1",
                "AUTH_ADMIN_SSO_REDIRECT_KEYWORD": "go-sso",
            },
        ):
            self._assert_redirects_to_sso(self._post_login("admin", "go-sso"))
            self._assert_normal_login(self._post_login("admin", "sso"))

    def test_redirect_login_unset(self):
        self._assert_normal_login(self._post_login("admin"))

    def test_redirect_login_invalid_value(self):
        with mock.patch.dict(os.environ, {"AUTH_ADMIN_SSO_REDIRECT_LOGIN": "foo"}):
            self._assert_normal_login(self._post_login("admin"))

    def test_redirect_login_default_login_override(self):
        with mock.patch.dict(
            os.environ,
            {
                "AUTH_ADMIN_SSO_REDIRECT_LOGIN": "1",
                "AUTH_ADMIN_SSO_DEFAULT_LOGIN": "shared",
            },
        ):
            self._assert_redirects_to_sso(self._post_login("shared"))
            self._assert_normal_login(self._post_login("admin"))

    def test_redirect_login_other_login(self):
        with mock.patch.dict(os.environ, {"AUTH_ADMIN_SSO_REDIRECT_LOGIN": "1"}):
            self._assert_normal_login(self._post_login("demo"))
