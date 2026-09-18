# Copyright 2026 KOBROS-TECH LTD
# License AGPL-3.0

import json
from contextlib import contextmanager
from unittest.mock import Mock, patch

from odoo.exceptions import AccessDenied
from odoo.tests.common import TransactionCase

NOTHING = object()


class TestAuthOAuthCodeFlowCommon(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        token_map = {
            "user_id": "id",
            "login": "login",
            "name": "name",
            "email": "email",
        }
        cls.provider = cls.env["auth.oauth.provider"].create(
            {
                "name": "GitHub Demo Provider",
                "client_id": "gh_client_id",
                "client_secret": "gh_client_secret",
                "token_map": json.dumps(token_map),
                "scope": "read:user user:email",
                "flow": "access_token_code",
                "auth_endpoint": "https://github.com/login/oauth/authorize",
                "token_endpoint": "https://github.com/login/oauth/access_token",
                "validation_endpoint": "https://api.github.com/user",
                "enabled": True,
                "body": "KOBROS-TECH Security Handshake",
            }
        )
        cls.github_uid = 12345678
        cls.user_login = "john@example.com"

    # -------------------------
    # Capture Token Exchange
    # -------------------------
    @contextmanager
    def _capture_token_exchange(self, return_value=NOTHING):
        class Capture:
            mock_response = Mock()
            captured_data = None

            def _mock_post(self, url, data=None, **kwargs):
                self.captured_data = data
                self.mock_response.status_code = 200
                self.mock_response.json.return_value = (
                    return_value
                    if return_value is not NOTHING
                    else {
                        "access_token": "gho_realistic_token_123",
                        "token_type": "bearer",
                        "scope": "read:user user:email",
                    }
                )
                return self.mock_response

        capture = Capture()
        with patch("requests.post", side_effect=capture._mock_post):
            yield capture

    # -------------------------
    # Capture User Info
    # -------------------------
    @contextmanager
    def _capture_user_info(self, return_value=NOTHING):
        class Capture:
            mock_response = Mock()
            captured_headers = None

            def _mock_get(self, url, headers=None, **kwargs):
                self.captured_headers = headers
                self.mock_response.status_code = 200
                self.mock_response.json.return_value = (
                    return_value
                    if return_value is not NOTHING
                    else {
                        "id": 12345678,
                        "login": "john-doe",
                        # email is False if it is private in GitHub
                        "email": "john@example.com",
                        "name": "John Doe",
                        "type": "User",
                    }
                )
                return self.mock_response

        capture = Capture()
        with patch("requests.get", side_effect=capture._mock_get):
            yield capture

    # -------------------------
    # Mock Odoo HTTP Request
    # -------------------------
    @contextmanager
    def _mock_odoo_request(self, return_value=NOTHING):
        """
        No MockRequest, just patch the global request object.
        """
        mock_request = Mock()
        mock_request.httprequest.url_root = "http://localhost:8069/"
        with patch("odoo.addons.auth_oidc.models.res_users.request", mock_request):
            yield mock_request

    # -------------------------
    # Mock Successful Signin
    # -------------------------
    @contextmanager
    def _mock_oauth_signin(self):
        def _mock_signin(self, provider, validation, params):
            # simulate successful login
            login = validation.get("email") or validation.get("login")
            user = self.search([("login", "=", login)], limit=1)
            if not user:
                user = self.create(
                    {
                        "name": validation.get("name") or login,
                        "login": login,
                        "email": validation.get("email") or login,
                        "oauth_uid": str(validation.get("user_id")),
                        "oauth_provider_id": provider,
                    }
                )
            return user.login

        with patch(
            (
                "odoo.addons.auth_oauth_multi_token.models."
                "res_users.ResUsers._auth_oauth_signin"
            ),
            _mock_signin,
        ):
            yield

    def test_01_github_handshake_success(self):
        with (
            self._capture_token_exchange() as token_cap,
            self._capture_user_info() as user_cap,
            self._mock_oauth_signin(),
            self._mock_odoo_request(),
        ):
            params = {
                "code": "dummy_code",
                "state": json.dumps(
                    {
                        "p": self.provider.id,
                        "d": self.env.cr.dbname,
                    }
                ),
            }
            db, login, token = self.env["res.users"].auth_oauth(
                self.provider.id, params
            )
            # Verify outgoing POST payload
            self.assertEqual(token_cap.captured_data["code"], "dummy_code")
            self.assertEqual(token_cap.captured_data["client_id"], "gh_client_id")
            # Verify Authorization header used in GET
            self.assertIn("Authorization", user_cap.captured_headers)
            self.assertEqual(
                user_cap.captured_headers["Authorization"],
                "Bearer gho_realistic_token_123",
            )
            # Verify result
            # email will be in the payload
            # only if (it is set in GitHub as public)
            self.assertEqual(login, self.user_login)
            self.assertEqual(token, "gho_realistic_token_123")
            # Verify DB binding
            user = self.env["res.users"].search([("login", "=", login)])
            self.assertEqual(user.oauth_uid, str(self.github_uid))

    def test_02_github_exchange_failure(self):
        error_response = {
            "error": "bad_verification_code",
            "error_description": "Invalid or expired code",
        }
        with (
            self._capture_token_exchange(return_value=error_response),
            self._mock_oauth_signin(),
            self._mock_odoo_request(),
        ):
            params = {"code": "invalid_code"}
            with self.assertLogs(
                "odoo.addons.auth_oauth_code_flow.models.res_users", level="ERROR"
            ):
                # assert the access error in the log
                with self.assertRaises(AccessDenied):
                    self.env["res.users"].auth_oauth(self.provider.id, params)

    def test_03_github_no_email(self):
        with (
            self._capture_token_exchange(),
            self._mock_oauth_signin(),
            self._capture_user_info(
                return_value={
                    "id": 12345678,
                    "login": "john-doe",
                    "email": False,
                    "name": "John Doe",
                }
            ),
            self._mock_odoo_request(),
        ):
            params = {
                "code": "dummy_code",
                "state": json.dumps(
                    {
                        "p": self.provider.id,
                        "d": self.env.cr.dbname,
                    }
                ),
            }
            db, login, token = self.env["res.users"].auth_oauth(
                self.provider.id, params
            )
            # fallback to login when email missing
            self.assertEqual(login, "john-doe")
