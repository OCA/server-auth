# Copyright 2026 360ERP (<https://www.360erp.com>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import http
from odoo.http import request

from odoo.addons.web.controllers.session import Session


class Session(Session):
    @http.route()
    def logout(self, redirect="/web"):
        request.env["impersonate.log"]._close_session_log()
        return super().logout(redirect=redirect)

    @http.route()
    def destroy(self):
        request.env["impersonate.log"]._close_session_log()
        return super().destroy()
