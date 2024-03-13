# Copyright 2024 360ERP (<https://www.360erp.com>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models
from odoo.http import request


class ResUsers(models.Model):
    _inherit = "res.users"

    def _mfa_url(self):
        """Needed to ensure that 'ignore_totp' is processed before entering
        the _mfa_url() of auth_totp_mail_enforce.
        """
        if request.session.get("ignore_totp"):
            return None
        return super()._mfa_url()
