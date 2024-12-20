# Copyright (C) 2013-Today GRAP (http://www.grap.coop)
# @author Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import exceptions
from odoo.tests import common, tagged
from odoo.tools import config


@tagged("post_install", "-at_install")
class TestAuthAdminPasskey(common.TransactionCase):
    """Tests for 'Auth Admin Passkey' Module"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))

        cls.ResUsers = cls.env["res.users"]

        cls.db = cls.env.cr.dbname

        cls.user_login = "auth_admin_passkey_user"
        cls.user_password = "Auth_admin_passkey_password*1"
        cls.sysadmin_passkey = "SysAdminPasskeyPa$$w0rd"
        # sysadmin_passkey encrypted with command:
        #   echo -n 'SysAdminPasskeyPa$$w0rd' | sha512sum
        cls.sysadmin_passkey_encrypted = (
            "364e3543996125e3408"
            "4b8eca00e328d4acdff9d24126c53624101812f8ed411fd38ecc9"
            "b64807adbf56b02d0315e209a61a193a85003488ca27af573801e65e"
        )
        cls.bad_password = "Bad_password*000001"
        cls.bad_login = "bad_login"

        user = cls.ResUsers.create(
            {
                "login": cls.user_login,
                "password": cls.user_password,
                "name": "auth_admin_passkey User",
            }
        )
        cls.user = user.with_user(user)

    def test_01_normal_login_succeed(self):
        self.user._check_credentials(
            {"type": "password", "password": self.user_password},
            {"interactive": True},
        )

    def test_02_normal_login_fail(self):
        with self.assertRaises(exceptions.AccessDenied):
            self.user._check_credentials(
                {"type": "password", "password": self.bad_password},
                {"interactive": True},
            )

    def test_03_normal_login_passkey_fail(self):
        # This should failed, because feature is disabled
        config["auth_admin_passkey_password"] = False
        config["auth_admin_passkey_password_sha512_encrypted"] = False
        with self.assertRaises(exceptions.AccessDenied):
            self.user._check_credentials(
                {"type": "password", "password": self.sysadmin_passkey},
                {"interactive": True},
            )

    def test_04_normal_login_passkey_succeed(self):
        # This should succeed, because feature is enabled
        config["auth_admin_passkey_password"] = self.sysadmin_passkey
        config["auth_admin_passkey_password_sha512_encrypted"] = False
        self.user._check_credentials(
            {"type": "password", "password": self.sysadmin_passkey},
            {"interactive": True},
        )

    def test_05_passkey_login_passkey_succeed(self):
        """[Bug #1319391]
        Test the correct behaviour of login with 'bad_login' / 'admin'"""
        with self.assertRaises(exceptions.AccessDenied):
            self.ResUsers.authenticate(
                self.db,
                {
                    "login": self.bad_login,
                    "password": self.sysadmin_passkey,
                    "type": "password",
                },
                {},
            )

    def test_06_normal_login_passkey_succeed_encrypted_password(self):
        # This should succeed, because feature is enabled
        config["auth_admin_passkey_password"] = self.sysadmin_passkey_encrypted
        config["auth_admin_passkey_password_sha512_encrypted"] = True
        self.user._check_credentials(
            {"type": "password", "password": self.sysadmin_passkey},
            {"interactive": True},
        )

    def test_07_email_notification_logic(self):
        """Test that the email notification logic works correctly."""
        config["auth_admin_passkey_sysadmin_email"] = "admin@example.com"
        config["auth_admin_passkey_send_to_user"] = True
        self.user.email = "user@example.com"

        with self.env.cr.savepoint():
            self.user._send_email_passkey(self.user)
            mail_ids = self.env["mail.mail"].search(
                [("email_to", "in", ["admin@example.com", "user@example.com"])]
            )
            self.assertEqual(
                len(mail_ids), 2, "Emails should be sent to both admin and user."
            )
            for mail in mail_ids:
                self.assertIn("Passkey used", mail.subject)

    def test_08_missing_sysadmin_passkey(self):
        """Test behavior when no passkey is configured."""
        config["auth_admin_passkey_password"] = False
        with self.assertRaises(exceptions.AccessDenied):
            self.user._check_credentials(
                {"type": "password", "password": self.sysadmin_passkey},
                {"interactive": True},
            )

    def test_09_empty_passkey_fails(self):
        """Test behavior when an empty passkey is provided."""
        config["auth_admin_passkey_password"] = self.sysadmin_passkey
        with self.assertRaises(exceptions.AccessDenied):
            self.user._check_credentials(
                {"type": "password", "password": ""},
                {"interactive": True},
            )

    def test_10_prepare_email_passkey(self):
        """Test email preparation logic."""
        subject, body_html = self.user._prepare_email_passkey(self.user)
        self.assertIn("Passkey used", subject)
        self.assertIn(self.user.login, body_html)
        self.assertIn("Login date", body_html)

    def test_11_incorrect_encrypted_password(self):
        """Test login fails with incorrect encrypted password."""
        config["auth_admin_passkey_password"] = self.sysadmin_passkey_encrypted
        config["auth_admin_passkey_password_sha512_encrypted"] = True
        with self.assertRaises(exceptions.AccessDenied):
            self.user._check_credentials(
                {"type": "password", "password": "WrongEncryptedPassword"},
                {"interactive": True},
            )
