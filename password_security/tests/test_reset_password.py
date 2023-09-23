# Copyright 2023 Onestein (<https://www.onestein.eu>)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import http
from odoo.exceptions import UserError
from odoo.tests.common import HttpCase, Opener, get_db_name, new_test_user, tagged


@tagged("-at_install", "post_install")
class TestPasswordSecurityReset(HttpCase):
    def setUp(self):
        super().setUp()
        self.env.company.password_policy_enabled = True

        # Create user with strong password: no error raised
        new_test_user(self.env, "jackoneill", password="!asdQWE12345_3")

    def reset_password(self, username):
        """Reset user password"""
        db = get_db_name()
        self.session = session = http.root.session_store.new()
        session.db = db
        http.root.session_store.save(session)

        self.opener = Opener(self.cr)
        self.opener.cookies["session_id"] = session.sid

        res_post = self.url_open(
            "/web/reset_password",
            data={
                "login": username,
                "name": username,
                "csrf_token": http.WebRequest.csrf_token(self),
            },
        )
        res_post.raise_for_status()

        return res_post

    def test_01_reset_password_fail(self):
        """It should fail when reset password below Minimum Hours"""
        # Enable check on Minimum Hours
        self.env.company.password_minimum = 24

        # Reset password
        response = self.reset_password("jackoneill")

        # Ensure we stay in the reset password page
        self.assertEqual(response.request.path_url, "/web/reset_password")
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            "Passwords can only be reset every %s hour(s). "
            "Please contact an administrator for assistance."
            % self.env.company.password_minimum,
            response.text,
        )

    def test_02_reset_password_success(self):
        """It should succeed when check on Minimum Hours is disabled"""

        # Disable check on Minimum Hours
        self.env.company.password_minimum = 0

        # Reset password
        response = self.reset_password("jackoneill")

        # Password reset instructions sent to user's email
        self.assertEqual(response.request.path_url, "/web/reset_password")
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            "An email has been sent with credentials to reset your password",
            response.text,
        )

    def test_03_reset_password_admin(self):
        """It should succeed when reset password is executed by Admin"""
        # Enable check on Minimum Hours
        self.env.company.password_minimum = 24

        # Executed by Admin: no error is raised
        self.assertTrue(self.env.user._is_admin())
        self.env["res.users"].reset_password("demo")

        # Executed by non-admin user: error is raised
        self.env = self.env(user=self.env.ref("base.user_demo"))
        self.assertFalse(self.env.user._is_admin())
        with self.assertRaises(UserError):
            self.env["res.users"].reset_password("demo")
