# Copyright 2026 Nimarosa
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from odoo import _, api, models
from odoo.tools import email_normalize

_logger = logging.getLogger(__name__)

# OpenID Connect claim, then the legacy Google tokeninfo spelling.
VERIFIED_EMAIL_CLAIMS = ("email_verified", "verified_email")
TRUTHY_CLAIM_VALUES = ("true", "1", "yes")


class ResUsers(models.Model):
    _inherit = "res.users"

    @api.model
    def _auth_oauth_validate(self, provider, access_token):
        # Link before the sign-in chain starts: auth_oauth_multi_token looks
        # the user up before calling super() and refuses the login when that
        # lookup was empty, even if the user got linked further down.
        validation = super()._auth_oauth_validate(provider, access_token)
        self._auth_oauth_autolink(provider, validation)
        return validation

    @api.model
    def _auth_oauth_signin(self, provider, validation, params):
        # The OpenID Connect flows of auth_oidc never call
        # _auth_oauth_validate. Linking before super() keeps a database with
        # signup enabled from trying to create a user with that login.
        # No access token: an auth_oauth_multi_token without the first-login
        # fix blanked it, and refuses this login whatever is linked here.
        if params.get("access_token"):
            self._auth_oauth_autolink(provider, validation)
        return super()._auth_oauth_signin(provider, validation, params)

    @api.model
    def _auth_oauth_autolink(self, provider, validation):
        """Link the OAuth identity to an existing user and return that user.

        Nothing is linked, and an empty recordset is returned, when the
        identity is already known or a guard refuses.
        """
        oauth_uid = validation["user_id"]
        if self.search_count(
            [("oauth_uid", "=", oauth_uid), ("oauth_provider_id", "=", provider)],
            limit=1,
        ):
            return self.browse()
        user = self._auth_oauth_autolink_find_user(provider, validation)
        if user:
            user.write({"oauth_provider_id": provider, "oauth_uid": oauth_uid})
            provider_name = user.oauth_provider_id.name
            _logger.info(
                "OAuth auto-link: user %s (id %s) linked to provider %s by "
                "verified e-mail.",
                user.login,
                user.id,
                provider_name,
            )
            # res.users is not a mail.thread; the chatter lives on its partner.
            user.partner_id.message_post(
                body=_(
                    "Linked to the %(provider)s account by verified e-mail on "
                    "first OAuth login.",
                    provider=provider_name,
                )
            )
        return user

    @api.model
    def _auth_oauth_autolink_find_user(self, provider, validation):
        """Return the only user this identity may be linked to, if any.

        Refusals are logged at INFO: they are expected, and the caller gets
        the stock ``AccessDenied`` without learning which guard refused.
        """
        no_user = self.browse()
        oauth_provider = self.env["auth.oauth.provider"].browse(provider)
        if not oauth_provider.autolink_by_email:
            return no_user
        if not self._auth_oauth_autolink_is_email_verified(validation):
            _logger.info(
                "OAuth auto-link refused for provider %s: e-mail not verified.",
                oauth_provider.name,
            )
            return no_user
        email = email_normalize(validation.get("email"))
        if not email:
            return no_user
        # ``=ilike`` treats ``_`` and ``%`` as wildcards: the normalized
        # comparison decides. Archived users are not searched.
        users = self.search([("login", "=ilike", email)]).filtered(
            lambda user: email_normalize(user.login) == email
        )
        if len(users) != 1:
            if users:
                _logger.info(
                    "OAuth auto-link refused: %s users share the login %s.",
                    len(users),
                    email,
                )
            return no_user
        if users.oauth_uid:
            _logger.info(
                "OAuth auto-link refused: user %s is already linked.", users.login
            )
            return no_user
        if users._has_group("base.group_system"):
            # Whoever controls that mailbox at the provider would become an
            # administrator: those users are linked by hand.
            _logger.info(
                "OAuth auto-link refused: user %s is an administrator.",
                users.login,
            )
            return no_user
        return users

    @api.model
    def _auth_oauth_autolink_is_email_verified(self, validation):
        # An absent claim is not a verified e-mail.
        for claim in VERIFIED_EMAIL_CLAIMS:
            value = validation.get(claim)
            if value is True:
                return True
            if isinstance(value, str) and value.strip().lower() in TRUTHY_CLAIM_VALUES:
                return True
        return False
