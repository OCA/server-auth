# Copyright 2026 Camptocamp SA
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo.tests import new_test_user
from odoo.tools import SQL

from odoo.addons.base.models.res_users import INDEX_SIZE

DAY = 60 * 60 * 24


class TrustedDeviceCommon:
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env["ir.config_parameter"].set_param("auth_totp.trusted_device_age", 7)
        cls.user = new_test_user(cls.env, "totp_user", groups="base.group_user")
        cls.Device = cls.env["auth_totp.device"].with_user(cls.user)

    def _devices(self):
        return self.env["auth_totp.device"].search([("user_id", "=", self.user.id)])

    def _new_device(self, expired=False):
        """Return the key of a new device, as created by the 2FA login page"""
        key = self.Device._generate("browser", "Test browser")
        if expired:
            self.env.cr.execute(
                SQL(
                    "UPDATE %s SET expiration_date = now() at time zone 'utc'"
                    " - INTERVAL '1 hour' WHERE index = %s",
                    SQL.identifier(self.Device._table),
                    key[:INDEX_SIZE],
                )
            )
        return key
