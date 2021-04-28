# Copyright 2021 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import json

from odoo.http import Controller, Response, request, route


class JWTTestController(Controller):
    @route(
        "/auth_jwt_test/whoami",
        type="http",
        auth="jwt_demo",
        csrf=False,
        cors="*",
        save_session=False,
    )
    def whoami(self):
        data = {}
        if request.jwt_partner_id:
            partner = request.env["res.partner"].browse(request.jwt_partner_id)
            data.update(name=partner.name, email=partner.email)
        return Response(json.dumps(data), content_type="application/json", status=200)
