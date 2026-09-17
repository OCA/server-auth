# Copyright (C) 2020 GlodoUK <https://glodo.uk/>
# Copyright (C) 2022 XCG Consulting <https://xcg-consulting.fr/>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AuthSamlRequest(models.TransientModel):
    _name = "auth_saml.request"
    _description = "SAML Outstanding Requests"
    _rec_name = "saml_request_id"

    saml_provider_id = fields.Many2one(
        "auth.saml.provider",
        string="SAML Provider that issued the token",
        required=True,
    )
    saml_request_id = fields.Char(
        "Current Request ID",
        required=True,
    )
