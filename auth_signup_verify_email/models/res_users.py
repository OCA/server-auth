# Copyright 2025 - Bigorna
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, models


class ResUsers(models.Model):
    _inherit = "res.users"

    @api.model
    def _auth_signup_required_fields(self):
        return ["name", "login", "email"]

    @api.model
    def _auth_signup_prepare_values(self, values):
        return {
            field: values.get(field)
            for field in self._auth_signup_required_fields()
            if field in values
        }
