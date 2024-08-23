# Copyright (C) 2024 Akretion (<http://www.akretion.com>).
# @author Kévin Roche <kevin.roche@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models
from odoo.http import request


class BaseModel(models.AbstractModel):
    _inherit = "base"

    def _prepare_create_values(self, vals_list):
        result_vals_list = super()._prepare_create_values(vals_list)
        if (
            request
            and request.session.impersonate_from_uid
            and "create_uid" in self._fields
        ):
            for vals in result_vals_list:
                vals["create_uid"] = request.session.impersonate_from_uid
        return result_vals_list

    def write(self, vals):
        """Overwrite the write_uid with the impersonating user"""
        res = super().write(vals)
        if (
            request
            and request.session.impersonate_from_uid
            and "write_uid" in self._fields
        ):
            self._fields["write_uid"].write(self, request.session.impersonate_from_uid)
        return res
