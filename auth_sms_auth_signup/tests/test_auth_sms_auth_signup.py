# Copyright 2019-2025 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from unittest import mock

from odoo import http
from odoo.tests import HOST, Opener, tagged

from odoo.addons.auth_sms.tests.common import HttpCaseSMS

_module_auth_sms = "odoo.addons.auth_sms"
_requests_class = _module_auth_sms + ".models.sms_provider.requests"


@tagged("post_install", "-at_install")
class TestAuthSmsAuthSignup(HttpCaseSMS):
    def test_auth_sms_auth_signup(self):
        self.session = http.root.session_store.new()
        self.opener = Opener(self.env.cr)
        self.opener.cookies.set("session_id", self.session.sid, domain=HOST, path="/")
        partner = self.demo_user.partner_id
        partner.signup_prepare(signup_type="reset")
        # 1, Get password reset form.
        url = self.base_url() + "/web/reset_password"
        params = {
            "token": partner.signup_token,
            "csrf_token": http.Request.csrf_token(self),
        }
        response = self.opener.get(
            url, params=params, timeout=12, headers=None, allow_redirects=True
        )
        path_url = self._bare_url(response)
        self.assertEqual(path_url, "/web/reset_password")
        # 2. Post and request sms code.
        with mock.patch(_requests_class + ".post") as mock_request_post:
            mock_request_post.return_value.json.return_value = {
                "originator": "originator",
            }
            params = {
                "token": partner.signup_token,
                "auth_sms_request_code": 1,
                "csrf_token": http.Request.csrf_token(self),
            }
            response = self.url_open(url, data=params)
            path_url = self._bare_url(response)
            self.assertEqual(path_url, "/web/reset_password")
            # retrieve the code to use from the mocked call
            self.code = mock_request_post.mock_calls[0][2]["data"]["body"]
            mock_request_post.assert_called_once()
        # 3. Set new password, while returning token.
        params = {
            "token": partner.signup_token,
            "password": "demo1",
            "password2": "demo1",
            "auth_sms_code": self.code,
            "csrf_token": http.Request.csrf_token(self),
        }
        response = self.url_open(url, data=params)
        path_url = self._bare_url(response)
        self.assertEqual(path_url, "/web/reset_password")

    def _bare_url(self, response):
        """Return bare url, that is withouth query parameters."""
        self.assertTrue(response.request.path_url)  # We have a path
        path_url = response.request.path_url
        if "?" in path_url:
            return path_url.split("?")[0]
        return path_url
