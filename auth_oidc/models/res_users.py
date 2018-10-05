# -*- coding: utf-8 -*-
# Copyright© 2016 ICTSTUDIO <http://www.ictstudio.eu>
# License: AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import models, api


class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.model
    def _auth_oauth_validate(self, provider, access_token):
        """ return the validation data corresponding to the access token """
        oauth_provider = self.env['auth.oauth.provider'].browse(provider)
        if oauth_provider.flow == 'id_token':
            return oauth_provider._parse_id_token(access_token)
        else:
            return super(ResUsers, self)._auth_oauth_validate()
    
    @api.model
    def auth_oauth(self, provider, params):
        id_token = params.get('id_token')
        if id_token:
            params['access_token'] = id_token
        return super(ResUsers, self).auth_oauth(provider, params)
