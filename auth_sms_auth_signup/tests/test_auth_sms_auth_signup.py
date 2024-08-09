# Copyright 2019 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from mock import patch

from odoo.addons.auth_sms.tests.common import Common


class TestAuthSmsAuthSignup(Common):
    def test_auth_sms_auth_signup(self):
        partner = self.demo_user.partner_id
        partner.signup_prepare(signup_type="reset")
        with self._request(
            "/web/reset_password",
            method="GET",
            data={
                "token": partner.signup_token,
            },
        ) as (request, endpoint):
            response = endpoint()
            self.assertTrue(response.qcontext["auth_sms_enabled"])
        with self._request(
            "/web/reset_password",
            data={
                "token": partner.signup_token,
                "auth_sms_request_code": 1,
            },
        ) as (request, endpoint), patch(
            "odoo.addons.auth_sms.models.sms_provider.requests.post",
        ) as mock_request_post:
            mock_request_post.return_value.json.return_value = {
                "originator": "originator",
            }
            response = endpoint()
            mock_request_post.assert_called_once()
        with self._request(
            "/web/reset_password",
            data={
                "token": partner.signup_token,
                "password": "demo1",
                "password2": "demo1",
                "auth_sms_code": mock_request_post.mock_calls[0][2]["data"]["body"],
            },
        ) as (request, endpoint):
            response = endpoint()
