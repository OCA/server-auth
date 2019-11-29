# Copyright (C) 2010-2016 XCG Consulting <http://odoo.consulting>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AuthSamlProvider(models.Model):
    _inherit = 'auth.saml.provider'

    create_user = fields.Boolean(
        string='Create User',
    )
