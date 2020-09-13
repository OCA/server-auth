# Copyright (C) 2010-2016 XCG Consulting <http://odoo.consulting>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
import passlib

from odoo.http import request
from odoo import api, fields, models, _, SUPERUSER_ID, tools
from odoo.exceptions import ValidationError, AccessDenied
from odoo.tools import config

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
    def get_saml_data(self, server):
        attributes = server.get_attributes()
        nameId = server.get_nameid()
        return {
            'timestamp': fields.Datetime.now(),
            'user_id': self.id,
            'login': self.login,
        }

    def _check_credentials(self, token):
        """Override to handle SAML auths."""
        credentials = request.session.get('saml_credentials')
        if credentials:
            # SAML login
            self._check_saml_credentials(credentials)
        elif not self._allow_saml_and_password():
            raise AccessDenied("SAML authentication required.")
        else:
            # Regular login
            super(ResUser, self)._check_credentials(token)
    
    @api.multi
    def _check_saml_credentials(self, credentials):
        timestamp = credentials.get('timestamp')
        user_id = credentials.get('user_id')
        dt = fields.Datetime.now() - fields.Datetime.from_string(timestamp)
        if dt.seconds > int(config.get('saml_timeout', '60')):
            raise AccessDenied("SAML authentication timed out.")
        if user_id != self.env.user.id:
            raise AccessDenied("SAML authentication user missmatch.")

    # TODO: Is there any point to this? Just check when authenticating...
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
                'auth_saml_ol.allow_saml.uid_and_internal_password', 'True'
            )
        )
