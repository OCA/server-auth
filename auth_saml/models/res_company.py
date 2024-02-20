# -*- coding: utf-8 -*-

from odoo import models, api, fields, _
class ResCompany(models.Model):
    _inherit = 'res.company'

    allow_saml_unsolicited_req = fields.Boolean()
