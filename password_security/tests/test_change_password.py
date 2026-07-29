# Copyright 2023 Onestein (<https://www.onestein.eu>)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from unittest import mock

from odoo import http
from odoo.exceptions import UserError, ValidationError
from odoo.tests.common import HOST, HttpCase, Opener, get_db_name, tagged


@tagged("-at_install", "post_install")
class TestPasswordSecurityChange(HttpCase):
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

    def test_01_empty_password_fail(self):
        """It should fail when changing password to empty"""

        # Log in: ensure we end up on the right page
        res_login = self.login("admin", "admin")
        self.assertEqual(res_login.request.path_url, "/odoo")
        self.assertEqual(res_login.status_code, 200)

        # Change password
        user = self.env["res.users"].search([("login", "=", "admin")], limit=1)
        self.assertTrue(user)
        with self.assertRaises(UserError):
            # UserError: Setting empty passwords is not allowed for security reasons
            user._change_password("")

    def test_02_change_password_fail(self):
        """It should fail when changing password to weak"""

        # Log in: ensure we end up on the right page
        res_login = self.login("admin", "admin")
        self.assertEqual(res_login.request.path_url, "/odoo")
        self.assertEqual(res_login.status_code, 200)

        # Change password: error is raised because it's too short
        user = self.env["res.users"].search([("login", "=", "admin")], limit=1)
        self.assertTrue(user)
        with self.assertRaises(UserError):
            user._change_password("admin")

        # Change password: error is raised by check password rules
        with self.assertRaises(ValidationError):
            user._change_password("adminadmin")

    def test_03_change_password_session_expired(self):
        """Session expires when password is changed"""

        # Log in: ensure we end up on the right page
        res_login = self.login("admin", "admin")
        self.assertEqual(res_login.request.path_url, "/odoo")
        self.assertEqual(res_login.status_code, 200)

        # Reload page: ensure we stay on the same page
        res_page1 = self.url_open("/web")
        res_page1.raise_for_status()
        self.assertEqual(res_page1.request.path_url, "/web")
        self.assertEqual(res_page1.status_code, 200)

        # Change password: no error raised
        user = self.env["res.users"].search([("login", "=", "admin")], limit=1)
        self.assertTrue(user)
        user._change_password("!asdQWE12345_3")

        # Try to reload page: user kicked out
        res_page2 = self.url_open("/web")
        res_page2.raise_for_status()
        self.assertTrue(res_page2.request.path_url.startswith("/web/login"))
        self.assertEqual(res_page2.status_code, 200)

    def test_04_change_password_check_password_history(self):
        """It should fail when chosen password was previously used"""

        # Set password history limit
        self.env["ir.config_parameter"].sudo().set_param("password_security.history", 3)
        user = self.env["res.users"].search([("login", "=", "admin")], limit=1)
        self.assertEqual(len(user.password_history_ids), 0)

        # Change password: password history records created
        user._change_password("!asdQWE12345_4")
        self.assertEqual(len(user.password_history_ids), 1)
        user._change_password("!asdQWE12345_5")
        self.assertEqual(len(user.password_history_ids), 2)
        user._change_password("!asdQWE12345_6")
        self.assertEqual(len(user.password_history_ids), 3)
        user._change_password("!asdQWE12345_7")
        self.assertEqual(len(user.password_history_ids), 4)

        # Log in: ensure we end up on the right page
        res_login = self.login("admin", "!asdQWE12345_7")
        self.assertEqual(res_login.request.path_url, "/odoo")

        # Change password: reuse password in history
        with self.assertRaises(UserError):
            user._change_password("!asdQWE12345_7")
        self.assertEqual(len(user.password_history_ids), 4)
        # Change password: reuse password in history
        with self.assertRaises(UserError):
            user._change_password("!asdQWE12345_6")
        self.assertEqual(len(user.password_history_ids), 4)
        # Change password: reuse password in history
        with self.assertRaises(UserError):
            user._change_password("!asdQWE12345_5")
        self.assertEqual(len(user.password_history_ids), 4)

        # Change password: reuse password in history but below limit
        user._change_password("!asdQWE12345_4")
        self.assertEqual(len(user.password_history_ids), 5)

        # Try to log in with old password: it fails
        res_login1 = self.login("admin", "!asdQWE12345_7")
        self.assertEqual(res_login1.request.path_url, "/web/login")

        # Log in with new password: ensure we end up on the right page
        res_login2 = self.login("admin", "!asdQWE12345_4")
        self.assertEqual(res_login2.request.path_url, "/odoo")
