# Copyright 2024 Akretion (http://www.akretion.com).
# @author Florian Mounier <florian.mounier@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import _
from odoo.exceptions import UserError
from odoo.http import Controller, request, route


class CrossConnectController(Controller):
    @route(
        ["/cross_connect_server/<int:server_id>"],
        methods=["GET"],
        type="http",
        auth="public",
    )
    def cross_connect(
        self,
        server_id,
        **params,
    ):
        server = request.env["cross.connect.server"].sudo().browse(server_id)
        if not server:
            raise UserError(_("Server not found"))

        url = server._get_cross_connect_url(request.params.get("redirect_url"))
        return request.redirect(url, local=False)
