# Copyright 2026 Camptocamp SA
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from datetime import timedelta

from odoo import fields
from odoo.tests import TransactionCase, new_test_user, tagged
from odoo.tools import SQL, mute_logger

from ..hooks import post_init_hook
from .common import DAY, TrustedDeviceCommon


# post_install: modules like mail add required fields on res.users
@tagged("post_install", "-at_install")
class TestAuthTotpDevice(TrustedDeviceCommon, TransactionCase):
    @mute_logger("odoo.addons.auth_totp_trusted_device_age.models.auth_totp_device")
    def test_trusted_device_age(self):
        icp = self.env["ir.config_parameter"]
        self.assertEqual(self.Device._get_trusted_device_age(), 7 * DAY)
        for value, days in (("1", 1), ("0", 90), ("-1", 90), ("x", 90)):
            icp.set_param("auth_totp.trusted_device_age", value)
            self.assertEqual(self.Device._get_trusted_device_age(), days * DAY)
        icp.set_param("auth_totp.trusted_device_age", False)
        self.assertEqual(self.Device._get_trusted_device_age(), 90 * DAY)

    def test_device_expiration_date(self):
        """A device created by a user expires after the trusted device age"""
        self._new_device()
        self.assertAlmostEqual(
            self._devices().expiration_date,
            fields.Datetime.now() + timedelta(days=7),
            delta=timedelta(minutes=1),
        )

    def test_device_not_capped_by_api_key_duration(self):
        """The device age applies to portal users, whose API keys last 1 day"""
        portal_user = new_test_user(self.env, "totp_portal", groups="base.group_portal")
        self.env["auth_totp.device"].with_user(portal_user)._generate(
            "browser", "Portal browser"
        )
        device = self.env["auth_totp.device"].search([("user_id", "=", portal_user.id)])
        self.assertAlmostEqual(
            device.expiration_date,
            fields.Datetime.now() + timedelta(days=7),
            delta=timedelta(minutes=1),
        )

    def test_gc_device_above_90_days(self):
        """Only the devices without expiration date expire after 90 days"""
        self.env["ir.config_parameter"].set_param("auth_totp.trusted_device_age", 180)
        self._new_device()
        self._new_device()
        old_devices = self._devices()
        self.env.cr.execute(
            SQL(
                "UPDATE %s SET create_date = create_date - INTERVAL '100 days'"
                " WHERE id IN %s",
                SQL.identifier(old_devices._table),
                tuple(old_devices.ids),
            )
        )
        self.env.cr.execute(
            SQL(
                "UPDATE %s SET expiration_date = NULL WHERE id = %s",
                SQL.identifier(old_devices._table),
                old_devices[0].id,
            )
        )
        self.env["auth_totp.device"]._gc_device()
        self.assertEqual(self._devices(), old_devices[1])

    def test_post_init_hook(self):
        self._new_device()
        device = self._devices()
        self.env.cr.execute(
            SQL(
                "UPDATE %s SET expiration_date = NULL,"
                " create_date = create_date - INTERVAL '2 days' WHERE id = %s",
                SQL.identifier(device._table),
                device.id,
            )
        )
        device.invalidate_recordset()
        post_init_hook(self.env)
        self.assertEqual(device.expiration_date, device.create_date + timedelta(days=7))
