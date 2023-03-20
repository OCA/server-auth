# Copyright 2023 Quartile Limited
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class ResUsers(models.Model):
    _inherit = "res.users"

    def _create_user_from_template(self, values):
        values["company_ids"] = [self.env.company.id]
        values["company_id"] = self.env.company.id
        return super()._create_user_from_template(values)

    def _signup_create_user(self, values):
        user = super()._signup_create_user(values)
        user.partner_id.company_id = self.env.company
        return user
