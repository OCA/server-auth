# Copyright (C) 2024 Akretion (<http://www.akretion.com>).
# @author Kévin Roche <kevin.roche@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models
from odoo.http import request


class BaseModel(models.AbstractModel):
    _inherit = "base"

    @api.model_create_multi
    def _create(self, data_list):
        res = super()._create(data_list)
        if (
            request
            and request.session.impersonate_from_uid
            and "create_uid" in self._fields
        ):
            for rec in res:
                rec["create_uid"] = request.session.impersonate_from_uid
        return res

    def write(self, vals):
        res = super().write(vals)
        if (
            request
            and request.session.impersonate_from_uid
            and "write_uid" in self._fields
        ):
            self._fields["write_uid"].write(self, request.session.impersonate_from_uid)
        return res
