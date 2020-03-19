# Copyright (C) 2010-2016 XCG Consulting <http://odoo.consulting>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    allow_saml_uid_and_internal_password = fields.Boolean(
        string='Allow SAML users to posess an Odoo password '
               '(warning: decreases security)'
    )

    @api.model
    def get_values(self):
        res = super().get_values()
        res["allow_saml_uid_and_internal_password"] = \
            self.env["res.users"]._allow_saml_and_password()
        return res

    def set_values(self):
        self.env['ir.config_parameter'].sudo().set_param(
            'auth_saml.allow_saml.uid_and_internal_password',
            self.allow_saml_uid_and_internal_password,
        )
        return super().set_values()
