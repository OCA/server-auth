# Copyright 2025 Hunki Enterprises BV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)

from unittest.mock import MagicMock, patch

from odoo.tests.common import TransactionCase


class TestAuthTotpBypassIpRange(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = cls.env.ref("base.user_demo")
        cls.user.totp_secret = "4242"

    def test_bypass(self):
        """Test that demo user can bypass MFA"""
        user = self.user.with_user(self.user)
        with patch(
            "odoo.addons.auth_totp_bypass_ip_range.models.res_users.request",
            new=MagicMock,
        ) as patched_request:
            patched_request.httprequest = MagicMock()
            patched_request.httprequest.environ = {"REMOTE_ADDR": "42.42.42.42"}
            self.assertTrue(user._mfa_type())
            self.assertTrue(user._mfa_url())
            self.env["ir.config_parameter"].set_param(
                "auth_totp_bypass_ip_range.networks",
                "1.1.1.0/16\n  42.42.42.42 42.42.1.0/24",
            )
            self.assertIsNone(user._mfa_type())
            self.assertIsNone(user._mfa_url())

    def test_misconfiguration(self):
        """
        Test that errors in configuration are logged but don't make it
        impossible to log in
        """
        user = self.user.with_user(self.user)
        with patch(
            "odoo.addons.auth_totp_bypass_ip_range.models.res_users.request",
            new=MagicMock,
        ) as patched_request, self.assertLogs("auth_totp_bypass_ip_range") as logger:
            patched_request.httprequest = MagicMock()
            patched_request.httprequest.environ = {"REMOTE_ADDR": "42.42.42.42"}
            self.env["ir.config_parameter"].set_param(
                "auth_totp_bypass_ip_range.networks",
                "wrong configuration",
            )
            self.assertTrue(user._mfa_type())
        self.assertTrue(
            any("wrong is not a valid network" in line for line in logger.output)
        )
