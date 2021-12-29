# Copyright 2021 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import json

from odoo.http import Controller, Response, request, route


class JWTTestController(Controller):
    @route(
        "/auth_jwt_demo/whoami",
        type="http",
        auth="jwt_demo",
        csrf=False,
        cors="*",
        save_session=False,
        methods=["GET", "OPTIONS"],
    )
    def whoami(self):
        data = {}
        if request.jwt_partner_id:
            partner = request.env["res.partner"].browse(request.jwt_partner_id)
            data.update(name=partner.name, email=partner.email)
        return Response(json.dumps(data), content_type="application/json", status=200)

    @route(
        "/auth_jwt_demo/keycloak/whoami",
        type="http",
        auth="jwt_demo_keycloak",
        csrf=False,
        cors="*",
        save_session=False,
        methods=["GET", "OPTIONS"],
    )
    def whoami_keycloak(self):
        """To use with the demo_keycloak validator.

        You can play with this using the browser app in tests/spa and the
        identity provider in tests/keycloak.
        """
        data = {}
        if request.jwt_partner_id:
            partner = request.env["res.partner"].browse(request.jwt_partner_id)
            data.update(name=partner.name, email=partner.email)
        return Response(json.dumps(data), content_type="application/json", status=200)

    @route(
        "/auth_jwt_demo/keycloak/whoami-public-or-jwt",
        type="http",
        auth="public_or_jwt_demo_keycloak",
        csrf=False,
        cors="*",
        save_session=False,
        methods=["GET", "OPTIONS"],
    )
    def whoami_public_or_keycloak(self):
        """To use with the demo_keycloak validator.

        You can play with this using the browser app in tests/spa and the
        identity provider in tests/keycloak.
        """
        data = {}
        if hasattr(request, "jwt_partner_id") and request.jwt_partner_id:
            partner = request.env["res.partner"].browse(request.jwt_partner_id)
            data.update(name=partner.name, email=partner.email)
        else:
            # public
            data.update(name="Anonymous")
        return Response(json.dumps(data), content_type="application/json", status=200)
