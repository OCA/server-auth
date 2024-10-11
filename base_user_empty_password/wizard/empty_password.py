# Copyright 2024 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class EmptyPasswordWizard(models.TransientModel):
    _name = "empty.password.wizard"
    _description = "Empty Password Wizard"

    user_ids = fields.Many2many("res.users", readonly=True)

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)

        if self.env.context.get("active_model") != "res.users":
            raise UserError(_("This can only be used on users."))

        res["user_ids"] = self.env.context.get("active_ids") or []

        return res

    def empty_password_button(self):
        self.ensure_one()
        self.user_ids._empty_password()
        return {"type": "ir.actions.client", "tag": "reload"}
