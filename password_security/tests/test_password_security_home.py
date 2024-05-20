# Copyright 2016 LasLabs Inc.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from datetime import datetime, timedelta
from unittest import mock

from werkzeug.urls import url_parse

from odoo.tests.common import HttpCase


@mock.patch("odoo.http.WebRequest.validate_csrf", return_value=True)
class LoginCase(HttpCase):
    def setUp(self):
        super(LoginCase, self).setUp()
        self.main_comp = self.env.ref("base.main_company")
        self.main_comp.password_policy_enabled = True

    def test_web_login_authenticate(self, *args):
        """It should allow authenticating by login"""
        response = self.url_open(
            "/web/login",
            {"login": "admin", "password": "admin"},
        )
        # Redirected to /web because it succeeded
        path = url_parse(response.url).path
        self.assertEqual(path, "/web")
        self.assertEqual(response.status_code, 200)

    def test_web_login_authenticate_fail(self, *args):
        """It should fail auth"""
        response = self.url_open(
            "/web/login",
            {"login": "admin", "password": "noadmin"},
        )
        self.assertIn(
            "Wrong login/password",
            response.text,
        )

    def test_web_login_expire_pass(self, *args):
        """It should expire password if necessary"""
        three_days_ago = datetime.now() - timedelta(days=3)
        with self.cursor() as cr:
            env = self.env(cr)
            user = env["res.users"].search([("login", "=", "admin")])
            user.password_write_date = three_days_ago
            user.company_id.password_expiration = 1
        response = self.url_open(
            "/web/login",
            {"login": "admin", "password": "admin"},
        )
        path = url_parse(response.url).path
        self.assertEqual(path, "/web/reset_password")
