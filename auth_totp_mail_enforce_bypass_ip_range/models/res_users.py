# Copyright 2025 Hunki Enterprises BV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)


from odoo import models


class ResUsers(models.Model):
    _inherit = "res.users"

    def _mfa_type(self):
        """
        Don't do MFA if the request comes from an IP that is configured to bypass it
        """
        if self._auth_totp_bypass_ip_range():
            return None
        return super()._mfa_type()

    def _mfa_url(self):
        """
        Don't do MFA if the request comes from an IP that is configured to bypass it
        """
        if self._auth_totp_bypass_ip_range():
            return None
        return super()._mfa_url()
