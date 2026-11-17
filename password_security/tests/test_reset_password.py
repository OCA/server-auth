# Copyright 2023 Onestein (<https://www.onestein.eu>)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from unittest import mock

from odoo.exceptions import UserError
from odoo.http.session import session_store
from odoo.tests.common import HOST, HttpCase, Opener, get_db_name, new_test_user, tagged


@tagged("-at_install", "post_install")
class TestPasswordSecurityResetPassword(HttpCase):
    def setUp(self):
        super().setUp()
        self.username = "jackoneill"
        self.passwd = "!asdQWE12345_3"
        new_test_user(self.env, self.username, password=self.passwd)

    def reset_password(self, username):
        """Reset the password through the web form"""
        self.session = session_store().new()
        # Since Odoo 19, Opener takes the HttpCase instance, not a cursor
        self.opener = Opener(self)
        self.opener.cookies.set("session_id", self.session.sid, domain=HOST, path="/")

        with mock.patch("odoo.http.router.db_filter") as db_filter:
            db_filter.side_effect = lambda dbs, host=None: [get_db_name()]
            res_post = self.url_open(
                "/web/reset_password",
                data={
                    "login": username,
                    "name": username,
                    "csrf_token": self.csrf_token(),
                },
            )
        res_post.raise_for_status()

        return res_post

    def test_01_reset_password_fail(self):
        """It should fail when resetting within the minimum delay"""
        min_hours = 24
        self.env["ir.config_parameter"].sudo().set_int(
            "password_security.minimum_hours", min_hours
        )

        response = self.reset_password(self.username)

        self.assertEqual(response.request.path_url, "/web/reset_password")
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            f"Passwords can only be reset every {min_hours} hour(s). "
            "Please contact an administrator for assistance.",
            response.text,
        )

    def test_02_reset_password_success(self):
        """It should succeed when the minimum delay check is disabled"""
        self.env["ir.config_parameter"].sudo().set_int(
            "password_security.minimum_hours", 0
        )

        response = self.reset_password(self.username)

        self.assertEqual(response.request.path_url, "/web/reset_password")
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            "Password reset instructions sent to your email",
            response.text,
        )

    def test_03_reset_password_admin(self):
        """It should succeed for an admin and fail for a non-admin user"""
        self.env["ir.config_parameter"].sudo().set_int(
            "password_security.minimum_hours", 24
        )

        # Admin can reset without restriction
        self.assertTrue(self.env.user._is_admin())
        self.env["res.users"].reset_password(self.username)

        # Non-admin user: an error is raised
        non_admin = self.env["res.users"].create(
            {
                "login": "test_non_admin",
                "name": "Test Non Admin",
                "password": "!asdQWE12345_4",
            }
        )
        with self.assertRaises(UserError):
            self.env["res.users"].with_user(non_admin).reset_password(self.username)
