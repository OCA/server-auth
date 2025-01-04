# Copyright 2025 Hunki Enterprises BV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)

from odoo.addons.auth_totp_bypass_ip_range.tests import test_auth_totp_bypass_ip_range


class TestAuthTotpMailEnforceBypassIpRange(
    test_auth_totp_bypass_ip_range.TestAuthTotpBypassIpRange
):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env["ir.config_parameter"].set_param("auth_totp.policy", "all_required")
