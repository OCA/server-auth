# Copyright 2023 Onestein (<https://www.onestein.eu>)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from unittest import mock

from odoo import http
from odoo.exceptions import UserError
from odoo.tests.common import HOST, HttpCase, Opener, get_db_name, new_test_user, tagged


@tagged("-at_install", "post_install")
class TestPasswordSecurityReset(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Create user with strong password: no error raised
        new_test_user(cls.env, "jackoneill", password="!asdQWE12345_3")

    def reset_password(self, username):
        """Reset user password"""
        self.session = http.root.session_store.new()
        self.opener = Opener(self)
        self.opener.cookies.set("session_id", self.session.sid, domain=HOST, path="/")

        with mock.patch("odoo.http.db_filter") as db_filter:
            db_filter.side_effect = lambda dbs, host=None: [get_db_name()]
            res_post = self.url_open(
                "/web/reset_password",
                data={
                    "login": username,
                    "name": username,
                    "csrf_token": http.Request.csrf_token(self),
                },
            )
        res_post.raise_for_status()

        return res_post

    def test_01_reset_password_fail(self):
        """It should fail when reset password below Minimum Hours"""
        # Enable check on Minimum Hours
        min_hours = 24
        self.env["ir.config_parameter"].sudo().set_param(
            "password_security.minimum_hours", min_hours
        )

        # Reset password
        response = self.reset_password("jackoneill")

        # Ensure we stay in the reset password page
        self.assertEqual(response.request.path_url, "/web/reset_password")
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            f"Passwords can only be reset every {min_hours} hour(s). "
            "Please contact an administrator for assistance.",
            response.text,
        )

    def test_02_reset_password_success(self):
        """It should succeed when check on Minimum Hours is disabled"""

        # Disable check on Minimum Hours
        self.env["ir.config_parameter"].sudo().set_param(
            "password_security.minimum_hours", 0
        )

        # Reset password
        response = self.reset_password("jackoneill")

        # Password reset instructions sent to user's email
        self.assertEqual(response.request.path_url, "/web/reset_password")
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            "Password reset instructions sent to your email",
            response.text,
        )

    def test_03_reset_password_admin(self):
        """It should succeed when reset password is executed by Admin"""
        # Enable check on Minimum Hours
        self.env["ir.config_parameter"].sudo().set_param(
            "password_security.minimum_hours", 24
        )

        # Use the user created in setUp: demo data is not loaded on the OCA
        # CI, so base.user_demo cannot be relied upon.
        user = self.env["res.users"].search([("login", "=", "jackoneill")])

        # Executed by Admin: no error is raised
        self.assertTrue(self.env.user._is_admin())
        self.env["res.users"].reset_password("jackoneill")

        # Executed by non-admin user: error is raised
        self.env = self.env(user=user)
        self.assertFalse(self.env.user._is_admin())
        with self.assertRaises(UserError):
            self.env["res.users"].reset_password("jackoneill")

    def test_04_reset_password_with_token(self):
        """It should reset the password when a signup token is provided

        Regression test: in 19.0 auth_signup.do_signup() gained a ``do_login``
        parameter, and web_auth_reset_password() calls it as
        ``self.do_signup(qcontext, do_login=False)``. An override keeping the
        old two-argument signature raises TypeError, breaking every password
        reset and every signup that goes through a token.
        """
        # Disable check on Minimum Hours so the reset is not blocked by it
        self.env["ir.config_parameter"].sudo().set_param(
            "password_security.minimum_hours", 0
        )

        user = self.env["res.users"].search([("login", "=", "jackoneill")])
        user.partner_id.signup_prepare(signup_type="reset")
        token = user.partner_id.sudo()._generate_signup_token()
        self.assertTrue(token, "The signup token should have been generated")

        new_password = "!asdQWE12345_4"
        self.session = http.root.session_store.new()
        self.opener = Opener(self)
        self.opener.cookies.set("session_id", self.session.sid, domain=HOST, path="/")

        with mock.patch("odoo.http.db_filter") as db_filter:
            db_filter.side_effect = lambda dbs, host=None: [get_db_name()]
            response = self.url_open(
                "/web/reset_password",
                data={
                    "token": token,
                    "login": "jackoneill",
                    "password": new_password,
                    "confirm_password": new_password,
                    "csrf_token": http.Request.csrf_token(self),
                },
            )

        self.assertEqual(response.status_code, 200)
        self.assertIn("Your password has been reset successfully.", response.text)
