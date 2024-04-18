# Copyright 2024 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo import fields, models


class EmptyPasswordWizard(models.TransientModel):
    _name = "empty.password.wizard"
    _description = "Empty Password Wizard"

    user_ids = fields.Many2many(
        "res.users", readonly=True, default=lambda w: w._default_user_ids()
    )

    def _default_user_ids(self):
        return (
            self.env.context.get("active_model") == "res.users"
            and self.env.context.get("active_ids")
            or []
        )

    def empty_password_button(self):
        self.ensure_one()
        self.user_ids._empty_password()
        return {"type": "ir.actions.client", "tag": "reload"}
