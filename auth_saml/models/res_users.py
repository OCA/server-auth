# Copyright (C) 2010-2016 XCG Consulting <http://odoo.consulting>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
import passlib

import lasso

from odoo import api, fields, models, _, SUPERUSER_ID, tools
from odoo.exceptions import ValidationError, AccessDenied

_logger = logging.getLogger(__name__)


class ResUser(models.Model):
    """Add SAML login capabilities to Odoo users.
    """

    _inherit = 'res.users'

    saml_provider_id = fields.Many2one(
        'auth.saml.provider',
        string='SAML Provider',
    )
    saml_uid = fields.Char(
        'SAML User ID',
        help="SAML Provider user_id",
    )

    @api.constrains('password', 'saml_uid')
    def check_no_password_with_saml(self):
        """Ensure no Odoo user posesses both an SAML user ID and an Odoo
        password. Except admin which is not constrained by this rule.
        """
        if not self._allow_saml_and_password():
            # Super admin is the only user we allow to have a local password
            # in the database
            if (self.password and self.saml_uid and
                    self.id is not SUPERUSER_ID):
                raise ValidationError(_("This database disallows users to "
                                        "have both passwords and SAML IDs. "
                                        "Errors for login %s") % (self.login))

    _sql_constraints = [('uniq_users_saml_provider_saml_uid',
                         'unique(saml_provider_id, saml_uid)',
                         'SAML UID must be unique per provider')]

    @api.multi
    def _auth_saml_validate(self, provider_id, token):
        """ return the validation data corresponding to the access token """

        p = self.env['auth.saml.provider'].browse(provider_id)

        # we are not yet logged in, so the userid cannot have access to the
        # fields we need yet
        login = p.sudo()._get_lasso_for_provider()
        matching_attribute = p.matching_attribute

        try:
            login.processAuthnResponseMsg(token)
        except (lasso.DsError, lasso.ProfileCannotVerifySignatureError):
            raise AccessDenied(_('Lasso Profile cannot verify signature'))
        except lasso.ProfileStatusNotSuccessError:
            raise AccessDenied(_('Profile Status failure'))

        try:
            login.acceptSso()
        except lasso.Error as error:
            raise Exception(
                'Invalid assertion : %s' % lasso.strError(error[0]))

        attrs = {}

        for att_statement in login.assertion.attributeStatement:
            for attribute in att_statement.attribute:
                name = None
                lformat = lasso.SAML2_ATTRIBUTE_NAME_FORMAT_BASIC
                nickname = None
                try:
                    name = attribute.name.decode('ascii')
                except Exception:
                    _logger.warning(
                        'sso_after_response: error decoding attribute name %s',
                        attribute.dump(),
                    )
                else:
                    try:
                        if attribute.nameFormat:
                            lformat = attribute.nameFormat.decode('ascii')
                        if attribute.friendlyName:
                            nickname = attribute.friendlyName
                    except Exception:
                        message = 'sso_after_response: name or format of an \
                            attribute failed to decode as ascii: %s'
                        _logger.warning(
                            message, attribute.dump(), exc_info=True
                        )
                    try:
                        if name:
                            if lformat:
                                if nickname:
                                    key = (name, lformat, nickname)
                                else:
                                    key = (name, lformat)
                            else:
                                key = name
                        attrs[key] = list()
                        for value in attribute.attributeValue:
                            content = [a.exportToXml() for a in value.any]
                            content = ''.join(content)
                            attrs[key].append(content.decode('utf8'))
                    except Exception:
                        message = 'sso_after_response: value of an \
                            attribute failed to decode as ascii: %s due to %s'
                        _logger.warning(
                            message, attribute.dump(), exc_info=True
                        )

        matching_value = None
        for k in attrs:
            if isinstance(k, tuple) and k[0] == matching_attribute:
                matching_value = attrs[k][0]
                break

        if not matching_value and matching_attribute == "subject.nameId":
            matching_value = login.assertion.subject.nameId.content

        elif not matching_value and matching_attribute != "subject.nameId":
            raise Exception(
                "Matching attribute %s not found in user attrs: %s" % (
                    matching_attribute, attrs))

        validation = {'user_id': matching_value}
        return validation

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
        user = self.search([
            ('saml_uid', '=', saml_uid),
            ('saml_provider_id', '=', provider),
        ])
        if len(user) != 1:
            raise AccessDenied()
        # now find if a token for this user/provider already exists
        token_ids = token_osv.search(
            [('saml_provider_id', '=', provider), ('user_id', '=', user.id)])

        if token_ids:
            token_ids.write({'saml_access_token': saml_response})
        else:
            token_osv.create({'saml_access_token': saml_response,
                              'saml_provider_id': provider,
                              'user_id': user.id})

        return user.login

    @api.model
    def auth_saml(self, provider, saml_response):

        validation = self._auth_saml_validate(provider, saml_response)

        # required check
        if not validation.get('user_id'):
            raise AccessDenied()

        # retrieve and sign in user
        login = self._auth_saml_signin(provider, validation, saml_response)

        if not login:
            raise AccessDenied()

        # return user credentials
        return self.env.cr.dbname, login, saml_response

    def _check_credentials(self, token):
        """Override to handle SAML auths.

        The token can be a password if the user has used the normal form...
        but we are more interested in the case when they are tokens
        and the interesting code is inside the "except" clause.
        """

        try:
            # Attempt a regular login (via other auth addons) first.
            super(ResUser, self)._check_credentials(token)

        except (AccessDenied, passlib.exc.PasswordSizeError):
            # since normal auth did not succeed we now try to find if the user
            # has an active token attached to his uid
            res = self.env['auth_saml.token'].sudo().search(
                [('user_id', '=', self.env.user.id),
                 ('saml_access_token', '=', token)])
            if not res:
                raise AccessDenied()

    @api.multi
    def _autoremove_password_if_saml(self):
        """Helper to remove password if it is forbidden for SAML users."""
        if self._allow_saml_and_password():
            return
        to_remove_password = self.filtered(
            lambda rec: rec.id != SUPERUSER_ID and rec.saml_uid and
            not (rec.password or rec.password_crypt)
        )
        to_remove_password.write({
            'password': False,
            'password_crypt': False,
        })

    @api.multi
    def write(self, vals):
        result = super().write(vals)
        self._autoremove_password_if_saml()
        return result

    @api.model_create_multi
    def create(self, vals_list):
        result = super().create(vals_list)
        result._autoremove_password_if_saml()
        return result

    @api.model
    def _allow_saml_and_password(self):
        """Know if both SAML and local password auth methods can coexist."""
        return tools.str2bool(
            self.env['ir.config_parameter'].sudo().get_param(
                'auth_saml.allow_saml.uid_and_internal_password', 'True'
            )
        )
