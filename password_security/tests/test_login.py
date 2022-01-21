# Copyright 2023 Onestein (<https://www.onestein.eu>)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from datetime import datetime, timedelta
from unittest import mock

from odoo import http
from odoo.exceptions import UserError, ValidationError
from odoo.modules.registry import Registry
from odoo.tests.common import HOST, HttpCase, Opener, get_db_name, new_test_user, tagged


@tagged("-at_install", "post_install")
class TestPasswordSecurityLogin(HttpCase):
    def setUp(self):
        super().setUp()
        self.username = "jackoneill"
        self.passwd = "!asdQWE12345_3"

        # Create user with strong password: no error raised
        new_test_user(self.env, self.username, password=self.passwd)

    def login(self, username, password):
        """Log in with provided credentials."""
        self.session = http.root.session_store.new()
        self.opener = Opener(self.env.cr)
        self.opener.cookies.set("session_id", self.session.sid, domain=HOST, path="/")

        with mock.patch("odoo.http.db_filter") as db_filter:
            db_filter.side_effect = lambda dbs, host=None: [get_db_name()]
            res_post = self.url_open(
                "/web/login",
                data={
                    "login": username,
                    "password": password,
                    "csrf_token": http.Request.csrf_token(self),
                },
            )
        res_post.raise_for_status()

        return res_post

    def test_01_create_user_fail(self):
        """It should fail when creating user with short password"""
        # Short password: UserError is raised
        with self.assertRaises(UserError):
            new_test_user(self.env, "new_user", password="abc")

    def test_02_create_user_fail(self):
        """It should fail when creating user with weak password"""
        # Weak password: ValidationError is raised
        with self.assertRaises(ValidationError):
            new_test_user(self.env, "new_user", password="abcdefgh")

    def test_03_web_login_success(self):
        """Allow authenticating by login"""

        # Log in
        response = self.login(self.username, self.passwd)

        # Ensure we end up on the right page
        self.assertEqual(response.request.path_url, "/odoo")
        self.assertEqual(response.status_code, 200)

    def test_04_web_login_fail(self):
        """Fail authenticating with wrong password"""

        # Try to log in
        response = self.login(self.username, "wrong")

        # Ensure we stay on the login page
        self.assertEqual(response.request.path_url, "/web/login")
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            "Wrong login/password",
            response.text,
        )

    def test_05_web_login_expire_pass(self):
        """It should expire password if necessary"""

        # Make password expired
        three_days_ago = datetime.now() - timedelta(days=3)

        with Registry(get_db_name()).cursor() as cr:
            env = self.env(cr)
            user = env["res.users"].search([("login", "=", self.username)])
            user.password_write_date = three_days_ago
            self.env["ir.config_parameter"].sudo().set_param(
                "password_security.expiration_days", 1
            )

        # Try to log in
        response = self.login(self.username, self.passwd)

        # Ensure we end up on the password reset page
        self.assertIn("/web/reset_password", response.request.path_url)

    def test_06_web_login_log_out_if_expired(self):
        """It should log out user if password expired"""

        # Log in
        response = self.login(self.username, self.passwd)

        # Ensure we end up on the right page
        self.assertEqual(response.request.path_url, "/odoo")
        self.assertEqual(response.status_code, 200)

        # Make password expired while still logged in
        three_days_ago = datetime.now() - timedelta(days=3)

        with Registry(get_db_name()).cursor() as cr:
            env = self.env(cr)
            user = env["res.users"].search([("login", "=", self.username)])
            user.password_write_date = three_days_ago
            self.env["ir.config_parameter"].sudo().set_param(
                "password_security.expiration_days", 1
            )

        # Try to access just a page
        req_page1 = self.url_open("/web")
        self.assertEqual(req_page1.request.path_url, "/web")
        self.assertEqual(req_page1.status_code, 200)

        # Try to log in again
        response = self.login(self.username, self.passwd)

        # Ensure we end up on the password reset page
        self.assertIn("/web/reset_password", response.request.path_url)

        # Try to access just a page: user kicked out
        req_page2 = self.url_open("/web")
        self.assertTrue(req_page2.request.path_url.startswith("/web/login"))
        self.assertEqual(req_page2.status_code, 200)

    def test_07_web_login_redirect(self):
        """It should redirect w/ hash to reset after expiration"""

        # Emulate password expired
        with mock.patch(
            "odoo.addons.password_security.models.res_users.ResUsers._password_has_expired"
        ) as func_password_has_expired:
            func_password_has_expired.return_value = True

            # Try to log in
            response = self.login(self.username, self.passwd)

        # Ensure we end up on the password reset page
        self.assertIn("/web/reset_password", response.request.path_url)

        # Try to access just a page: user kicked out
        req_page = self.url_open("/web")
        self.assertTrue(req_page.request.path_url.startswith("/web/login"))
        self.assertEqual(req_page.status_code, 200)
