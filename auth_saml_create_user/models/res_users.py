# © 2019 Savoir-faire Linux
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import logging

from odoo import api, models
from odoo.exceptions import AccessDenied

_logger = logging.getLogger(__name__)


class Users(models.Model):
    _inherit = "res.users"

    @api.multi
    def _auth_saml_signin(self, provider, validation, saml_response):
        """ retrieve and sign into openerp the user corresponding to provider
        and validated access token

            :param provider: saml provider id (int)
            :param validation: result of validation of access token (dict)
            :param saml_response: saml parameters response from the IDP
            :return: user login (str)
            :raise: openerp.exceptions.AccessDenied if signin failed

            This method can be overridden to add alternative signin methods.
        """
        token_osv = self.env['auth_saml.token']
        saml_uid = validation['user_id']

        user_ids = self.search(
            [('saml_uid', '=', saml_uid), ('saml_provider_id', '=', provider)])

        if user_ids:
            # TODO replace assert by proper raise... asserts do not execute in
            # production code...
            assert len(user_ids) == 1
            user = user_ids[0]

            # now find if a token for this user/provider already exists
            token_ids = token_osv.search(
                [('saml_provider_id', '=', provider), ('user_id', '=', user.id)])

            if token_ids:
                token_ids.write({'saml_access_token': saml_response})
            else:
                token_osv.create({'saml_access_token': saml_response,
                                  'saml_provider_id': provider,
                                  'user_id': user.id
                                  })
            return user.login
        elif self.env['auth.saml.provider'].browse(provider).create_user:
            _logger.debug("Creating new Odoo user \"%s\" from LDAP" % saml_uid)
            # This following line is to create user with default template
            # values = self.map_ldap_attributes(conf, saml_uid, ldap_entry)
            SudoUser = self.env['res.users'].sudo()
            # if conf['user']:
            #    values['active'] = True
            #   user_id = SudoUser.browse(conf['user'][0]).copy(default=values).id
            new_user = SudoUser.create({
                'name': saml_uid,
                'login': saml_uid,
                'saml_provider_id': provider,
                'company_id': self.env['res.company'].sudo().browse(1).id,
                'saml_uid': saml_uid
            })
            new_user.write({'saml_uid': saml_uid})
            token_osv.create({'saml_access_token': saml_response,
                              'saml_provider_id': provider,
                              'user_id': new_user.id
                              })
            return new_user.login
        else:
            raise AccessDenied()
