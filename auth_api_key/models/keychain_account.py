# -*- coding: utf-8 -*-
# Copyright 2018 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class KeychainAccount(models.Model):

    _inherit = 'keychain.account'

    namespace = fields.Selection(
        selection_add=[('auth_api_key', 'Search Engine Backend')])

    @api.multi
    def _auth_api_key_validate_data(self, data):
        return True

    @api.multi
    def _auth_api_key_init_data(self):
        return {}
