# Copyright (C) 2024 Akretion (<http://www.akretion.com>).
# @author Kévin Roche <kevin.roche@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models
from odoo.http import request


class BaseModel(models.AbstractModel):
    _inherit = "base"

    def _prepare_create_values(self, vals_list):
        result_vals_list = super()._prepare_create_values(vals_list)
        # Keep core attachment access semantics intact.
        # For temporary/generated attachments (often without res_model/res_id),
        # read access falls back to creator ownership. Rewriting create_uid to
        # the original impersonator can make the active impersonated user lose
        # access immediately in the same flow (e.g. compose email after report).
        if self._name == "ir.attachment":
            return result_vals_list
        if (
            request
            and request.session.get("impersonate_from_uid")
            and "create_uid" in self._fields
        ):
            for vals in result_vals_list:
                vals["create_uid"] = request.session.get("impersonate_from_uid")
        return result_vals_list

    def write(self, vals):
        """Overwrite the write_uid with the impersonating user"""
        res = super().write(vals)
        if self._name == "ir.attachment":
            return res
        if (
            request
            and request.session.get("impersonate_from_uid")
            and "write_uid" in self._fields
        ):
            self._fields["write_uid"].write(
                self, request.session.get("impersonate_from_uid")
            )
        return res
