# -*- coding: utf-8 -*-
# Copyright 2026 Binovo IT Human Project SL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import http, fields
from odoo.http import request
from odoo.addons.web.controllers.session import Session


class SessionWebsite(Session):

    @http.route('/web/session/logout', type='http', auth="none", website=True, multilang=False, sitemap=False)
    def logout(self, redirect='/web'):
        if request.session.impersonate_from_uid:
            request.env["impersonate.log"].sudo().browse(
                request.session.impersonate_log_id
            ).write(
                {
                    "date_end": fields.datetime.now(),
                }
            )
        return super().logout(redirect=redirect)
