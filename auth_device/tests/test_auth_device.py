# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging

from psycopg2.errors import UniqueViolation

from odoo import exceptions
from odoo.tests import tagged
from odoo.tests.common import SavepointCase


@tagged("post_install", "-at_install")
class TestAuthDevice(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.ResUsers = cls.env["res.users"]
        cls.ResPartner = cls.env["res.partner"]
        cls.user_device_code = "123456789012"
        cls.bad_device_code = "345678098765"
        cls.partner_user = cls.ResPartner.create(
            {
                "name": "User Device Code",
                "email": "user.device@example.com",
            }
        )
        cls.user = cls.ResUsers.create(
            {
                "name": "User Device Code",
                "login": "user_device",
                "email": "device@user.login",
                "partner_id": cls.partner_user.id,
                "device_code": cls.user_device_code,
                "is_allowed_to_connect_with_device": True,
            }
        )
        cls.user = cls.user.with_user(cls.user)

    def test_01_normal_login_succeed(self):
        self.user._check_credentials(self.user_device_code, {"interactive": True})

    def test_02_normal_login_fail(self):
        with self.assertRaises(exceptions.AccessDenied):
            self.user._check_credentials(self.bad_device_code, {"interactive": True})

    def test_03_missing_device_code(self):
        with self.assertRaises(AssertionError):
            self.user._check_credentials("", {"interactive": True})

    def test_04_duplicate_device_code(self):
        partner_2 = self.partner_user = self.ResPartner.create(
            {
                "name": "Duplicate Device Code",
                "email": "duplicate.device.code@example.com",
            }
        )
        with self.assertLogs(level=logging.ERROR):
            with self.assertRaises(UniqueViolation):
                self.ResUsers.create(
                    {
                        "name": "Duplicate Device Code",
                        "login": "duplicate_device_code",
                        "email": "device@duplicate.login",
                        "partner_id": partner_2.id,
                        "device_code": self.user_device_code,
                        "is_allowed_to_connect_with_device": True,
                    }
                )

    def test_05_not_allowed_to_connect(self):
        self.user.sudo().is_allowed_to_connect_with_device = False
        with self.assertRaises(exceptions.AccessDenied):
            self.user._check_credentials(self.user_device_code, {"interactive": True})
