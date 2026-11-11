# Copyright 2026 spomata
# License: AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

import logging

from odoo import api, models
from odoo.tools import escape_psql

_logger = logging.getLogger(__name__)


class ResUsers(models.Model):
    _inherit = "res.users"

    @api.model
    def _auth_oauth_signin(self, provider, validation, params):
        self._auth_oauth_link_user_by_verified_email(provider, validation)
        return super()._auth_oauth_signin(provider, validation, params)

    @api.model
    def _auth_oauth_link_user_by_verified_email(self, provider, validation):
        """Link an unknown subject to an existing user on its first login.

        The email is only used once, to bootstrap the link: afterwards the user
        is found by (oauth_provider_id, oauth_uid) like any other oauth user.
        """
        oauth_provider = self.env["auth.oauth.provider"].browse(provider)
        if not oauth_provider.link_user_by_verified_email:
            return
        oauth_uid = validation.get("user_id")
        if not oauth_uid or self.search_count(
            [("oauth_uid", "=", oauth_uid), ("oauth_provider_id", "=", provider)],
            limit=1,
        ):
            # an ordinary login, nothing to link
            return
        email = validation.get("email")
        if not email:
            _logger.info(
                "Not linking oauth subject of provider %s: no email claim.", provider
            )
            return
        # strict check, some providers send email_verified as a string
        if validation.get("email_verified") is not True:
            _logger.info(
                "Not linking oauth subject of provider %s: email %s is not "
                "verified (email_verified=%r).",
                provider,
                email,
                validation.get("email_verified"),
            )
            return
        # match the login only: it is the credential and only administrators
        # can change it, while users can edit their own email
        user = self.search([("login", "=ilike", escape_psql(email))])
        if not user:
            _logger.info(
                "Not linking oauth subject of provider %s: no active user has "
                "%s as login.",
                provider,
                email,
            )
            return
        if len(user) > 1:
            _logger.warning(
                "Not linking oauth subject of provider %s: %s users have "
                "its email as login.",
                provider,
                len(user),
            )
            return
        if user.oauth_uid:
            _logger.warning(
                "Not linking oauth subject of provider %s to user %s: user is "
                "already linked to another subject.",
                provider,
                user.login,
            )
            return
        if user._has_group("base.group_system"):
            _logger.warning(
                "Not linking oauth subject of provider %s to user %s: "
                "administrators must be linked manually.",
                provider,
                user.login,
            )
            return
        _logger.info(
            "Linking oauth subject of provider %s to user %s by verified email.",
            provider,
            user.login,
        )
        user.write({"oauth_provider_id": provider, "oauth_uid": oauth_uid})
