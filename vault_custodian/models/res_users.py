# © 2026 Nitrokey GmbH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ResUsers(models.Model):
    _inherit = "res.users"

    has_vault_key = fields.Boolean(
        compute="_compute_has_vault_key",
        search="_search_has_vault_key",
        help="Whether the user has vault keys configured",
    )

    @api.depends("keys")
    def _compute_has_vault_key(self):
        for rec in self:
            rec.has_vault_key = bool(rec.sudo().keys)

    @api.model
    def _search_has_vault_key(self, operator, value):
        if operator not in ("=", "!=") or not isinstance(value, bool):
            raise ValueError(self.env._("Unsupported search operator"))

        users_with_keys = self.env["res.users.key"].sudo().search([]).mapped("user_id")
        has_key = (operator == "=") == value
        return [("id", "in" if has_key else "not in", users_with_keys.ids)]
