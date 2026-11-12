# Copyright © 2025 XCG SAS
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import http

from odoo.addons.web.controllers.session import Session


class SessionLogout(Session):
    # If it was possible the default redirect would be changed.
    # That does not work when http_routing is installed or any module that would change
    # logout.
    @http.route("/web/session/logout", type="http", auth="none")
    def logout(self, redirect="/web"):  # pylint: disable=unused-argument
        return super().logout("web/logout_successful")
