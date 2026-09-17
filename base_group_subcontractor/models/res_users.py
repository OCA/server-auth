# Copyright 2026 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, models


class ResUsers(models.Model):
    _inherit = "res.users"

    def _compute_share(self):
        # Consider as non shared those users of subcontractor group
        res = super()._compute_share()
        user_group_id = self.env["ir.model.data"]._xmlid_to_res_id(
            "base_group_subcontractor.group_subcontractor"
        )
        self.filtered_domain([("groups_id", "in", [user_group_id])]).share = False
        return res

    @api.readonly
    def has_group(self, group_ext_id: str) -> bool:
        # trick this method to test also the belonging to the new subcontractor group
        alt_value = False
        if group_ext_id == "base.group_user":
            alt_value = super().has_group(
                "base_group_subcontractor.group_subcontractor"
            )
        return alt_value or super().has_group(group_ext_id)
