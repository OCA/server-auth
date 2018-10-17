# -*- coding: utf-8 -*-
# Copyright 2018 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class KeychainAccount(models.Model):

    _inherit = 'keychain.account'

    namespace = fields.Selection(
        selection_add=[('auth_api_key', 'Authentification Api key')])
