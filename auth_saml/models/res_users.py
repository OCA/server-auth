# Copyright (C) 2020 GlodoUK <https://www.glodo.uk>
# Copyright (C) 2010-2016 XCG Consulting <http://odoo.consulting>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

import passlib
import os

from odoo import SUPERUSER_ID, _, api, fields, models, tools
from odoo.exceptions import AccessDenied, ValidationError

_logger = logging.getLogger(__name__)

def gen_password(length=8, charset="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*()"):
    random_bytes = os.urandom(length)
    len_charset = len(charset)
    indices = [int(len_charset * (ord(byte) / 256.0)) for byte in random_bytes]
    return "".join([charset[index] for index in indices])

class ResUser(models.Model):
    """
    Add SAML login capabilities to Odoo users.
    """

    _inherit = "res.users"

    saml_provider_id = fields.Many2one("auth.saml.provider", string="SAML Provider",)
    saml_uid = fields.Char("SAML User ID", help="SAML Provider user_id",)

    @api.constrains("password", "saml_uid")
    def check_no_password_with_saml(self):
        """Ensure no Odoo user posesses both an SAML user ID and an Odoo
        password. Except admin which is not constrained by this rule.
        """
        if not self._allow_saml_and_password():
            # Super admin is the only user we allow to have a local password
            # in the database
            if self.password and self.saml_uid and self.id is not SUPERUSER_ID:
                raise ValidationError(
                    _(
                        "This database disallows users to "
                        "have both passwords and SAML IDs. "
                        "Errors for login %s"
                    )
                    % (self.login)
                )

    _sql_constraints = [
        (
            "uniq_users_saml_provider_saml_uid",
            "unique(saml_provider_id, saml_uid)",
            "SAML UID must be unique per provider",
        )
    ]

    def _auth_saml_validate(self, provider_id, token):
        p = self.env["auth.saml.provider"].sudo().browse(provider_id)
        return p._validate_auth_response(token)

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
        token_osv = self.env["auth_saml.token"]
        saml_uid = validation["user_id"]
        user = self.search(
            [("saml_uid", "=", saml_uid), ("saml_provider_id", "=", provider)]
        )
        if len(user) != 1:
            _logger.info("Could not find matching saml user for '%s' against provider %d", saml_uid, provider)
            raise AccessDenied()
        # now find if a token for this user/provider already exists
        token_ids = token_osv.search(
            [("saml_provider_id", "=", provider), ("user_id", "=", user.id)]
        )

        if token_ids:
            token_ids.write({"saml_access_token": saml_response})
        else:
            _logger.info("Creating auth_saml.token")
            token_ids = token_osv.create(
                {
                    "saml_access_token": saml_response,
                    "saml_provider_id": provider,
                    "user_id": user.id,
                }
            )

        if validation.get("mapped_attrs", {}):
            user.write(validation.get("mapped_attrs", {}))

        return user.login

    @api.model
    def auth_saml(self, provider, saml_response):
        validation = self._auth_saml_validate(provider, saml_response)

        # required check
        if not validation.get("user_id"):
            _logger.info("Failed to validate saml response")
            raise AccessDenied()

        # retrieve and sign in user
        login = self._auth_saml_signin(provider, validation, saml_response)

        if not login:
            _logger.info("Did not get any login back from _auth_saml_signin")
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
            res = (
                self.env["auth_saml.token"]
                .sudo()
                .search(
                    [
                        ("user_id", "=", self.env.user.id),
                        ("saml_access_token", "=", token),
                    ]
                )
            )
            if not res:
                _logger.info("Did not find auth_saml.token")
                raise AccessDenied()

    def _autoremove_password_if_saml(self):
        """Helper to remove password if it is forbidden for SAML users."""
        if self._allow_saml_and_password():
            return
        to_remove_password = self.filtered(
            lambda rec: rec.id != SUPERUSER_ID
            and rec.saml_uid
            and not (rec.password or rec.password_crypt)
        )
        to_remove_password.write(
            {"password": gen_password(length=20)}
        )

    def write(self, vals):
        result = super().write(vals)
        self._autoremove_password_if_saml()
        self._ensure_saml_token_exists()
        return result

    @api.model_create_multi
    def create(self, vals_list):
        result = super().create(vals_list)
        result._autoremove_password_if_saml()
        result._ensure_saml_token_exists()
        return result

    @api.model
    def _allow_saml_and_password(self):
        """Can both SAML and local password auth methods can coexist."""
        return tools.str2bool(
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("auth_saml.allow_saml.uid_and_internal_password", "True")
        )

    def _ensure_saml_token_exists(self):
        # workaround for Odoo not seeing the newly created auth_saml.token on
        # the very first login
        model_token = self.env["auth_saml.token"].sudo()
        for record in self.filtered(lambda r: r.saml_provider_id):
            token = model_token.search(
                [
                    ("user_id", "=", record.id),
                    ("saml_provider_id", "=", record.saml_provider_id.id),
                ]
            )
            if not token:
                model_token.create(
                    {
                        "user_id": record.id,
                        "saml_provider_id": record.saml_provider_id.id,
                    }
                )
