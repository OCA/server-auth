# Copyright 2026 360ERP (<https://www.360erp.com>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AuthUserRoleMapping(models.Model):
    _name = "auth.user.role.mapping"
    _description = "Identity Role Mapping"
    _rec_name = "attribute"
    _order = "attribute"
    _clear_cache_name = "default"

    attribute = fields.Char(
        string="Identity Attribute",
        help=(
            "The payload attribute to check (e.g., department, "
            "groups, eduPersonAffiliation)."
        ),
        required=True,
    )
    operator = fields.Selection(
        selection=[("equals", "equals"), ("contains", "contains")],
        default="equals",
        required=True,
        help="The operator to check the attribute against the value.",
    )
    value = fields.Char(help="The value to check the attribute against.", required=True)
    role_id = fields.Many2one(
        "res.users.role",
        help="The Odoo role to assign.",
        required=True,
        ondelete="cascade",
    )

    @api.model
    @api.ormcache()
    def _get_all_mappings_cached(self):
        """Fetch all mappings and cache them as native dicts for fast evaluation."""
        mappings = self.sudo().search_fetch(
            [], ["attribute", "operator", "value", "role_id"]
        )
        return [
            {
                "attribute": m.attribute,
                "operator": m.operator,
                "value": m.value,
                "role_id": m.role_id.id,
            }
            for m in mappings
        ]
