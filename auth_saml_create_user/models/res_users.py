# © 2019 Savoir-faire Linux
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import api, models
import random

_logger = logging.getLogger(__name__)
s = "abcdefghijklmnopqrstuvwxyz034567890ABCDEFGHIJKLMNOPQRSTUVWXYZ!@#$%^&*()?"
passlen = 16


class ResUsers(models.Model):
    _inherit = "res.users"

    @api.multi
    def _auth_saml_signin(self, provider, validation, saml_response):
        saml_uid = validation['user_id']
        user_ids = self.search(
            [('saml_uid', '=', saml_uid), ('saml_provider_id', '=', provider)])
        if self.check_if_create_user(provider) and not user_ids:
            self.create_user(saml_uid, provider)
        return super()._auth_saml_signin(provider, validation, saml_response)

    def check_if_create_user(self, provider):
        return self.env['auth.saml.provider'].browse(provider).create_user

    def create_user(self, saml_uid, provider):
        _logger.debug("Creating new Odoo user \"%s\" from SAML" % saml_uid)
        SudoUser = self.env['res.users'].sudo()
        new_user = SudoUser.create({
            'name': saml_uid,
            'login': saml_uid,
            'saml_provider_id': provider,
            'password': "".join(random.sample(s, passlen)),
            'company_id': self.env['res.company'].sudo().browse(1).id,
        })
        new_user.write(
            {'saml_uid': saml_uid})
