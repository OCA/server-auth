# Copyright (C) 2010-2016, 2022 XCG Consulting <http://odoo.consulting>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    allow_saml_unsolicited_req = fields.Boolean(
        string="Allow SAML Unsolicited Requests",
        help="Allow IdP-initiated authentication requests without prior "
        "AuthnRequest from SP",
    )
