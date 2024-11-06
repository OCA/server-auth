# Copyright 2019-2025 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from unittest import mock

from lxml.html import document_fromstring

from odoo import http
from odoo.tests import HOST, Opener, get_db_name, tagged

from .common import HttpCaseSMS

_module_ns = "odoo.addons.auth_sms"
_requests_class = _module_ns + ".models.sms_provider.requests"
_users_class = _module_ns + ".models.res_users.ResUsers"


@tagged("post_install", "-at_install")
class TestAuthSms(HttpCaseSMS):
    def test_auth_sms_login_no_2fa(self):
        # admin doesn't have sms verification turned on
        response = self._login_user(self.admin_user.login, self.admin_user.login)
        self.assertEqual(response.request.path_url, "/web")
        self.assertEqual(response.status_code, 200)

    def test_auth_sms_login_no_error(self):
        # first request: login
        response = self._mock_login_user(self.demo_user.login, self.password)
        self.assertEqual(response.request.path_url, "/web/login")
        # fill the correct code
        response = self._enter_code(self.code)
        self.assertEqual(response.request.path_url, "/web")

    def test_auth_sms_login(self):
        # first request: login
        response = self._mock_login_user(self.demo_user.login, self.password)
        self.assertEqual(response.request.path_url, "/web/login")
        # then fill in a wrong code
        response = self._enter_code("wrong code")
        self.assertEqual(response.request.path_url, "/auth_sms/code")
        # fill the correct code
        response = self._enter_code(self.code)
        self.assertEqual(response.request.path_url, "/web")

    def test_auth_sms_rate_limit(self):
        """Request codes until we hit the rate limit."""
        # Make sure there are no codes left.
        self.env["auth_sms.code"].search([("user_id", "=", self.demo_user.id)]).unlink()
        for _i in range(10):
            response = self._mock_login_user(self.demo_user.login, self.password)
            self.assertEqual(response.request.path_url, "/web/login")
        # 10th time should result in error (assuming default limit).
        # DO not call with _mock, as sms will not be send anyway.
        response = self._login_user(self.demo_user.login, self.password)
        self.assertEqual(response.request.path_url, "/web/login")
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            "Rate limit for SMS exceeded",
            response.text,
        )

    def _mock_login_user(self, login, password):
        """Login as a specific user (assume password is same as login)."""
        with mock.patch(_requests_class + ".post") as mock_request_post:
            mock_request_post.return_value.json.return_value = {
                "originator": "originator",
            }
            response = self._login_user(login, password)
            # retrieve the code to use from the mocked call
            self.code = mock_request_post.mock_calls[0][2]["data"]["body"]
            # retrieve the secret from the response, if present.
            document = document_fromstring(response.content)
            secret_inputs = document.xpath("//input[@name='secret']")
            self.secret = secret_inputs[0].get("value") if secret_inputs else None
        return response

    def _login_user(self, login, password):
        """Login as a specific user."""
        # Code largely taken from password_security/tests/test_login.py.
        # session must be part of self, because of csrf_token method.
        self.session = http.root.session_store.new()
        self.opener = Opener(self.env.cr)
        self.opener.cookies.set("session_id", self.session.sid, domain=HOST, path="/")
        with mock.patch("odoo.http.db_filter") as db_filter:
            db_filter.side_effect = lambda dbs, host=None: [get_db_name()]
            # The response returned here is not the odoo.http.Response class,
            # but the requests.Response.
            response = self.url_open(
                "/web/login",
                data={
                    "login": login,
                    "password": password,
                    "csrf_token": http.Request.csrf_token(self),
                },
            )
        response.raise_for_status()
        return response

    def _enter_code(self, code):
        """Enter code from sms (wrong or correct)."""
        return self.url_open(
            "/auth_sms/code",
            data={
                "secret": self.secret,
                "user_login": self.demo_user.login,
                "password": code,
                "csrf_token": http.Request.csrf_token(self),
            },
        )
