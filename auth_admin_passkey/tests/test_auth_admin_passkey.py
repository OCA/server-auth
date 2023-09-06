# Copyright (C) 2013-Today GRAP (http://www.grap.coop)
# @author Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import exceptions
from odoo.tests import common
from odoo.tools import config


@common.post_install(True)
class TestAuthAdminPasskey(common.TransactionCase):
    """Tests for 'Auth Admin Passkey' Module"""

    def setUp(self):
        super(TestAuthAdminPasskey, self).setUp()

        self.ResUsers = self.env["res.users"]

        self.db = self.env.cr.dbname

        self.user_login = "auth_admin_passkey_user"
        self.user_login_block_admin_password = "auth_admin_passkey_block"
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
        user_block_admin_password = self.ResUsers.create(
            {
                "login": self.user_login_block_admin_password,
                "password": self.user_password,
                "name": "auth_admin_passkey_block User",
                "block_admin_passkey": True,
            }
        )
        self.user = user.sudo(user)
        self.user_block_admin_password = user.sudo(user_block_admin_password)

    def test_01_normal_login_succeed(self):
        self.user._check_credentials(self.user_password)

    def test_02_normal_login_fail(self):
        with self.assertRaises(exceptions.AccessDenied):
            self.user._check_credentials(self.bad_password)

    def test_03_normal_login_passkey_fail(self):
        # This should failed, because feature is disabled
        config["auth_admin_passkey_password"] = False
        with self.assertRaises(exceptions.AccessDenied):
            self.user._check_credentials(self.sysadmin_passkey)

    def test_04_normal_login_passkey_succeed(self):
        # This should succeed, because feature is enabled
        config["auth_admin_passkey_password"] = self.sysadmin_passkey
        self.user._check_credentials(self.sysadmin_passkey)

    def test_05_passkey_login_passkey_succeed(self):
        """[Bug #1319391]
        Test the correct behaviour of login with 'bad_login' / 'admin'"""
        with self.assertRaises(exceptions.AccessDenied):
            self.ResUsers.authenticate(
                self.db, self.bad_login, self.sysadmin_passkey, {}
            )

    def test_06_passkey_block_user(self):
        # This should failed, because user has the option blocked
        with self.assertRaises(exceptions.AccessDenied):
            self.user_block_admin_password._check_credentials(self.sysadmin_passkey)
