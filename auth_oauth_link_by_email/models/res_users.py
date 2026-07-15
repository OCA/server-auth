# Copyright 2026 Heligrafics <https://www.heligrafics.net>
# License: AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

import logging

from odoo import api, models

_logger = logging.getLogger(__name__)


class ResUsers(models.Model):
    _inherit = "res.users"

    @api.model
    def _oauth_link_user_by_email(self, provider, oauth_uid, email, access_token):
        user = self.search([("login", "=", email)], limit=1)
        if not user:
            _logger.warning(
                "OAuth link by email: no user found with login=%s, skipping.",
                email,
            )
            return None
        user.write(
            {
                "oauth_provider_id": provider,
                "oauth_uid": oauth_uid,
                "oauth_access_token": access_token,
            }
        )
        _logger.info(
            "OAuth link by email: user '%s' linked to provider %s with oauth_uid=%s.",
            user.login,
            provider,
            oauth_uid,
        )
        return user

    @api.model
    def _auth_oauth_signin(self, provider, validation, params):
        oauth_uid = validation["user_id"]
        already_linked = self.search(
            [
                ("oauth_uid", "=", oauth_uid),
                ("oauth_provider_id", "=", provider),
            ],
            limit=1,
        )
        if not already_linked:
            email = validation.get("email")
            if email:
                linked_user = self._oauth_link_user_by_email(
                    provider, oauth_uid, email, params["access_token"]
                )
                if linked_user:
                    return linked_user.login
        return super()._auth_oauth_signin(provider, validation, params)
