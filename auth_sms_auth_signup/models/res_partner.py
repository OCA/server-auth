# Copyright 2019 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import api, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    @api.model
    def signup_retrieve_info(self, token):
        result = super().signup_retrieve_info(token)
        partner = self._signup_retrieve_partner(token, raise_exception=True)
        result["auth_sms_enabled"] = partner.user_ids[:1].auth_sms_enabled
        return result
