# Copyright 2024 360ERP (<https://www.360erp.com>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from unittest import mock

from odoo import http
from odoo.tests.common import HOST, HttpCase, Opener, get_db_name, new_test_user, tagged
from odoo.tools import config


@tagged("-at_install", "post_install")
class TestAuthAdminPasskeyTotpMailEnforce(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.username = "jackoneill"
        cls.passwd = "AnyUserPa$$w0rd"
        cls.sysadmin_passkey = "SysAdminPasskeyPa$$w0rd"

        # Create a new session
        cls.session = http.root.session_store.new()

        # Create test user with 2FA
        cls.user = new_test_user(cls.env, cls.username, password=cls.passwd)
        cls.user.write({"totp_secret": "test"})

    def login(self, username, password):
        """Log in with provided credentials."""
        self.opener = Opener(self.env.cr)
        self.opener.cookies.set("session_id", self.session.sid, domain=HOST, path="/")

        with mock.patch("odoo.http.db_filter") as db_filter:
            db_filter.side_effect = lambda dbs, host=None: [get_db_name()]
            res_post = self.url_open(
                "/web/login",
                timeout=1200000,
                data={
                    "login": username,
                    "password": password,
                    "csrf_token": http.Request.csrf_token(self),
                },
            )
        res_post.raise_for_status()

        return res_post

    def test_01_web_login_with_user_password_and_2fa(self):
        """
        If two-factor authentication enabled, authenticating with user
        password redirects to /web/login/totp
        """

        # Reset session (login page displayed)
        response = self.url_open("/web/session/logout")
        self.assertEqual(response.request.path_url, "/web/login")

        # Enable passkey and set auth_admin_passkey_ignore_totp = True
        config["auth_admin_passkey_password"] = self.sysadmin_passkey
        config["auth_admin_passkey_ignore_totp"] = True

        # Two-factor authentication enabled
        self.assertTrue(self.user.totp_enabled)

        # User logs in with user password
        response = self.login(self.username, self.passwd)

        # Ensure we end up on the right page (user logged in)
        self.assertEqual(response.request.path_url, "/web/login/totp")
        self.assertEqual(response.status_code, 200)

    def test_02_web_login_with_passkey_and_2fa(self):
        """
        If two-factor authentication enabled, authenticating with passkey
        does not redirect to /web/login/totp
        """

        # Reset session (login page displayed)
        response = self.url_open("/web/session/logout")
        self.assertEqual(response.request.path_url, "/web/login")

        # Enable passkey and set auth_admin_passkey_ignore_totp = True
        config["auth_admin_passkey_password"] = self.sysadmin_passkey
        config["auth_admin_passkey_ignore_totp"] = True
        config["auth_admin_passkey_password_sha512_encrypted"] = False

        # Two-factor authentication enabled
        self.assertTrue(self.user.totp_enabled)

        # User logs in with passkey
        response = self.login(self.username, self.sysadmin_passkey)

        # Ensure we end up on the right page (user logged in)
        self.assertEqual(response.request.path_url, "/web")
        self.assertEqual(response.status_code, 200)
