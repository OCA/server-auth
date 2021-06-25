# Copyright (C) 2010-2016 XCG Consulting <http://odoo.consulting>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    allow_saml_uid_and_internal_password = fields.Boolean(
        "Allow SAML users to posess an Odoo password (warning: decreases security)",
        config_parameter="auth_saml.allow_saml_uid_and_internal_password",
    )
