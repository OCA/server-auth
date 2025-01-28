# Copyright (C) 2020 GlodoUK <https://www.glodo.uk>
# Copyright (C) 2010-2016 XCG Consulting <http://odoo.consulting>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from typing import Set  # noqa

import passlib

from odoo import SUPERUSER_ID, _, api, fields, models, modules, tools
from odoo.exceptions import AccessDenied, ValidationError

from .ir_config_parameter import ALLOW_SAML_UID_AND_PASSWORD

_logger = logging.getLogger(__name__)


class ResUser(models.Model):
    """
    Add SAML login capabilities to Odoo users.
    """

    _inherit = "res.users"

    saml_ids = fields.One2many("res.users.saml", "user_id")

    def _auth_saml_validate(self, provider_id: int, token: str, base_url: str = None):
        provider = self.env["auth.saml.provider"].sudo().browse(provider_id)
        return provider._validate_auth_response(token, base_url)

    def _auth_saml_signin(self, provider: int, validation: dict, saml_response) -> str:
        """Sign in Odoo user corresponding to provider and validated access token.

        :param provider: SAML provider id
        :param validation: result of validation of access token
        :param saml_response: saml parameters response from the IDP
        :return: user login
        :raise: odoo.exceptions.AccessDenied if signin failed

        This method can be overridden to add alternative signin methods.
        """
        saml_uid = validation["user_id"]
        user_saml = self.env["res.users.saml"].search(
            [("saml_uid", "=", saml_uid), ("saml_provider_id", "=", provider)],
            limit=1,
        )
        user = user_saml.user_id
        if len(user) != 1:
            raise AccessDenied()

        with modules.registry.Registry(self.env.cr.dbname).cursor() as new_cr:
            new_env = api.Environment(new_cr, self.env.uid, self.env.context)
            # Update the token. Need to be committed, otherwise the token is not visible
            # to other envs, like the one used in login_and_redirect
            user_saml.with_env(new_env).write({"saml_access_token": saml_response})

        if validation.get("mapped_attrs", {}):
            # Only write field that changes to avoid generating Security Update on users
            # when login/email changes (from mail module)
            vals = {}
            for key, value in validation.get("mapped_attrs", {}).items():
                # If the value or the field value is not a str,
                # avoid comparison and write anyway
                if (
                    not isinstance(value, str)
                    or not isinstance(user[key], str)
                    or user[key] != value
                ):
                    vals[key] = value
            if vals:
                user.write(vals)

        return user.login

    @api.model
    def auth_saml(self, provider: int, saml_response: str, base_url: str = None):
        validation = self._auth_saml_validate(provider, saml_response, base_url)

        # required check
        if not validation.get("user_id"):
            raise AccessDenied()

        # retrieve and sign in user
        login = self._auth_saml_signin(provider, validation, saml_response)

        if not login:
            raise AccessDenied()

        # return user credentials
        return self.env.cr.dbname, login, saml_response

    def _check_credentials(self, credential, env):
        """Override to handle SAML auths.

        The token can be a password if the user has used the normal form...
        but we are more interested in the case when they are tokens
        and the interesting code is inside the "except" clause.
        """
        try:
            # Attempt a regular login (via other auth addons) first.
            return super()._check_credentials(credential, env)
        except (AccessDenied, passlib.exc.PasswordSizeError):
            if not (credential["type"] == "saml_token" and credential["token"]):
                raise
            passwd_allowed = (
                env["interactive"] or not self.env.user._rpc_api_keys_only()
            )
            if passwd_allowed and self.env.user.active:
                # since normal auth did not succeed we now try to find if the user
                # has an active token attached to his uid
                token = (
                    self.env["res.users.saml"]
                    .sudo()
                    .search(
                        [
                            ("user_id", "=", self.env.user.id),
                            ("saml_access_token", "=", credential["token"]),
                        ]
                    )
                )
                if token:
                    return {
                        "uid": self.env.user.id,
                        "auth_method": "saml",
                        "mfa": "default",
                    }
            raise AccessDenied() from None

    @api.model
    def _saml_allowed_user_ids(self) -> Set[int]:  # noqa
        """Users that can have a password even if the option to disallow it is set.

        It includes superuser and the admin if it exists.
        """
        allowed_users = {SUPERUSER_ID}
        user_admin = self.env.ref("base.user_admin", False)
        if user_admin:
            allowed_users.add(user_admin.id)
        return allowed_users

    @api.model
    def allow_saml_and_password(self) -> bool:
        """Can both SAML and local password auth methods coexist."""
        return tools.str2bool(
            self.env["ir.config_parameter"]
            .sudo()
            .get_param(ALLOW_SAML_UID_AND_PASSWORD)
        )

    def _set_password(self):
        """Inverse method of the password field."""
        # Redefine base method to block setting password on users with SAML ids
        # And also to be able to set password to a blank value
        if not self.allow_saml_and_password():
            saml_users = self.filtered(
                lambda user: user.sudo().saml_ids
                and user.id not in self._saml_allowed_user_ids()
                and user.password
            )
            if saml_users:
                # same error as an api.constrains because it is a constraint.
                # a standard constrains would require the use of SQL as the password
                # field is obfuscated by the base module.
                raise ValidationError(
                    _(
                        "This database disallows users to "
                        "have both passwords and SAML IDs. "
                        "Error for logins %s"
                    )
                    % saml_users.mapped("login")
                )
        # handle setting password to NULL
        blank_password_users = self.filtered(lambda user: user.password is False)
        non_blank_password_users = self - blank_password_users
        if non_blank_password_users:
            # pylint: disable=protected-access
            super(ResUser, non_blank_password_users)._set_password()
        if blank_password_users:
            blank_password_users._set_password_blank()
        return

    def _set_password_blank(self):
        """Set the password to a value that prohibits logging."""
        # Use SQL to blank the password to avoid sending security messages (done in
        # mail module) to end users.
        _logger.debug("Removing password from %s user(s)", len(self.ids))
        # similar to what Odoo does in Users._set_encrypted_password
        self.env.cr.execute(
            "UPDATE res_users SET password = NULL WHERE id IN %s",
            (tuple(self.ids),),
        )
        self.invalidate_recordset(fnames=["password"])

    def allow_saml_and_password_changed(self):
        """Called after the parameter is changed."""
        if not self.allow_saml_and_password():
            # sudo because the user doing the parameter change might not have the right
            # to search or write users
            blank_password_users = self.sudo().search(
                [
                    "&",
                    ("saml_ids", "!=", False),
                    ("id", "not in", list(self._saml_allowed_user_ids())),
                ]
            )
            blank_password_users._set_password_blank()
