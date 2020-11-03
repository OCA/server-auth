# Copyright (C) 2013-Today GRAP (http://www.grap.coop)
# @author Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import exceptions
from odoo.tests import common, tagged
from odoo.tools import config


@tagged("post_install", "-at_install")
class TestAuthAdminPasskey(common.TransactionCase):
    """Tests for 'Auth Admin Passkey' Module"""

    def setUp(self):
        super(TestAuthAdminPasskey, self).setUp()

        self.ResUsers = self.env["res.users"]

        self.db = self.env.cr.dbname

        self.user_login = "auth_admin_passkey_user"
        self.user_password = "Auth_admin_passkey_password*1"
        self.sysadmin_passkey = "SysAdminPasskeyPa$$w0rd"
        self.bad_password = "Bad_password*000001"
        self.bad_login = "bad_login"

        user = self.ResUsers.create(
            {
                "login": self.user_login,
                "password": self.user_password,
                "name": "auth_admin_passkey User",
            }
        )
        self.user = user.with_user(user)

    def test_01_normal_login_succeed(self):
        self.user._check_credentials(self.user_password, {"interactive": True})

    def test_02_normal_login_fail(self):
        with self.assertRaises(exceptions.AccessDenied):
            self.user._check_credentials(self.bad_password, {"interactive": True})

    def test_03_normal_login_passkey_fail(self):
        # This should failed, because feature is disabled
        config["auth_admin_passkey_password"] = False
        with self.assertRaises(exceptions.AccessDenied):
            self.user._check_credentials(self.sysadmin_passkey, {"interactive": True})

    def test_04_normal_login_passkey_succeed(self):
        # This should succeed, because feature is enabled
        config["auth_admin_passkey_password"] = self.sysadmin_passkey
        self.user._check_credentials(self.sysadmin_passkey, {"interactive": True})

    def test_05_passkey_login_passkey_succeed(self):
        """[Bug #1319391]
        Test the correct behaviour of login with 'bad_login' / 'admin'"""
        with self.assertRaises(exceptions.AccessDenied):
            self.ResUsers.authenticate(
                self.db, self.bad_login, self.sysadmin_passkey, {}
            )
