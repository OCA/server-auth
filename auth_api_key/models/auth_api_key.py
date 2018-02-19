# -*- coding: utf-8 -*-
# Copyright 2018 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, tools


class AuthApiKey(models.Model):
    _name = 'auth.api.key'
    _inherit = 'keychain.backend'
    _backend_name = 'auth_api_key'

    @api.model
    def _default_user_id(self):
        return self.env.user

    user_id = fields.Many2one(
        'res.users',
        'User',
        required=True,
        help="The user used to execute the code into Odoo when user is called "
             "with this api key.",
        default=_default_user_id
    )

    @api.multi
    def _inverse_password(self):
        self.retrieve_id_by_api_key.clear_cache(self)
        return super(AuthApiKey, self)._inverse_password()

    @api.model
    def retrieve_from_api_key(self, api_key):
        return self.browse(self.retrieve_id_by_api_key().get(api_key, []))

    @api.model
    @tools.ormcache('self.env.uid', 'self._backend_name', 'self._name')
    def retrieve_id_by_api_key(self):
        keychain_account = self.env['keychain.account']
        keychain_accounts = keychain_account.search([
            ('namespace', '=', self._backend_name),
            ('technical_name', 'like', self._name)
        ])
        res = {}
        for key in keychain_accounts:
            _id = int(key.technical_name.split(',')[1])
            api_key = key._get_password()
            res[api_key] = _id
        return res
