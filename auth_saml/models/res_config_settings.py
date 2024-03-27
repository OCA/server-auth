# Copyright (C) 2010-2016, 2022 XCG Consulting <http://odoo.consulting>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models

from .ir_config_parameter import ALLOW_SAML_UID_AND_PASSWORD


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    allow_saml_uid_and_internal_password = fields.Boolean(
        "Allow SAML users to possess an Odoo password (warning: decreases security)",
        config_parameter=ALLOW_SAML_UID_AND_PASSWORD,
    )

    allow_saml_unsolicited_req = fields.Boolean(
            related='company_id.allow_saml_unsolicited_req', readonly=False
    )

