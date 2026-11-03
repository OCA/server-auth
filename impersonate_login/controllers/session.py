# Copyright 2026 360ERP (<https://www.360erp.com>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import http
from odoo.http import request

from odoo.addons.web.controllers.session import Session


class Session(Session):
    def _impersonate_readonly(self):
        """Serve these routes with a read/write cursor.

        The web module declares both routes as readonly, but the impersonate
        log has to be closed before the session is destroyed. Letting Odoo
        replay the request on a read/write cursor is not an option: the
        session is already logged out by then, so the log id would be lost.

        A callable is used, like the web module does for /web/dataset/call_kw,
        because a plain ``readonly=False`` makes Odoo log a warning about an
        override changing the read/write mode of the route.
        """
        return False

    @http.route(readonly=_impersonate_readonly)
    def logout(self, redirect="/odoo"):
        request.env["impersonate.log"]._close_session_log()
        return super().logout(redirect=redirect)

    @http.route(readonly=_impersonate_readonly)
    def destroy(self):
        request.env["impersonate.log"]._close_session_log()
        return super().destroy()
