# Copyright (C) 2024 Akretion (<http://www.akretion.com>).
# @author Kévin Roche <kevin.roche@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models
from odoo.http import request


class Http(models.AbstractModel):
    _inherit = "ir.http"

    @classmethod
    def _pre_dispatch(cls, rule, args):
        res = super()._pre_dispatch(rule, args)
        # Keep track of the activity of an impersonated session, so that its
        # log can still be closed if the session ends without a logout.
        request.env["impersonate.log"]._touch_session_log()
        return res

    def session_info(self):
        session_info = super().session_info()
        session_info.update(
            {
                "is_impersonate_user": request.env.user._is_impersonate_user(),
                "impersonate_from_uid": request.session.get("impersonate_from_uid"),
            }
        )
        return session_info
