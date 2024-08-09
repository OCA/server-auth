# Copyright 2019 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from mock import patch

from .common import Common


class TestAuthSms(Common):
    def test_auth_sms_login_no_2fa(self):
        # admin doesn't have sms verification turned on
        with self._request(
            "/web/login",
            method="POST",
            data={
                "login": self.env.user.login,
                "password": self.env.user.login,
            },
        ) as (request, endpoint):
            response = endpoint()
            self.assertFalse(response.template)

    def test_auth_sms_login(self):
        # first request: login
        with self._request(
            "/web/login",
            data={
                "login": self.demo_user.login,
                "password": self.demo_user.login,
            },
        ) as (request, endpoint), patch(
            "odoo.addons.auth_sms.models.sms_provider.requests.post",
        ) as mock_request_post:
            mock_request_post.return_value.json.return_value = {
                "originator": "originator",
            }
            response = endpoint()
            self.assertEqual(response.template, "auth_sms.template_code")
            self.assertTrue(request.session["auth_sms.password"])
            mock_request_post.assert_called_once()
            self.odoo_root.session_store.save(request.session)

        # then fill in a wrong code
        with self._request(
            "/auth_sms/code",
            data={
                "secret": response.qcontext["secret"],
                "user_login": response.qcontext["login"],
                "password": "wrong code",
            },
        ) as (request, endpoint):
            response = endpoint()
            self.assertEqual(response.template, "auth_sms.template_code")
            self.assertTrue(response.qcontext["error"])

        # fill the correct code
        with self._request(
            "/auth_sms/code",
            data={
                "secret": response.qcontext["secret"],
                "user_login": response.qcontext["login"],
                "password": mock_request_post.mock_calls[0][2]["data"]["body"],
            },
        ) as (request, endpoint):
            response = endpoint()
            self.assertFalse(response.is_qweb)
            self.assertTrue(response.data)

    def test_auth_sms_rate_limit(self):
        # reuqest codes until we hit the rate limit
        with self._request(
            "/web/login",
            data={
                "login": self.demo_user.login,
                "password": self.demo_user.login,
            },
        ) as (request, endpoint), patch(
            "odoo.addons.auth_sms.models.sms_provider.requests.post",
        ) as mock_request_post:
            mock_request_post.return_value.json.return_value = {
                "originator": "originator",
            }
            for i in range(9):
                response = endpoint()
                self.assertNotIn("error", response.qcontext)
            response = endpoint()
            self.assertTrue(response.qcontext["error"])
