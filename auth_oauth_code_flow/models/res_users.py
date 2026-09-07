# Copyright 2026 KOBROS-TECH LTD <https://www.kobros-tech.com>
# License: AGPL-3.0 or later (http://www.gnu.org)

import logging

from odoo import api, models
from odoo.exceptions import AccessDenied

_logger = logging.getLogger(__name__)


class ResUsers(models.Model):
    _inherit = "res.users"

    @api.model
    def auth_oauth(self, provider, params):
        oauth_provider = self.env["auth.oauth.provider"].browse(provider)
        # 1. Handle specific flow (OAuth2 Code Flow)
        if oauth_provider.flow == "access_token_code":
            # Perform the handshake (POST exchange)
            access_token, id_token = self._auth_oauth_get_tokens_auth_code_flow(
                oauth_provider, params
            )
            if not access_token:
                _logger.error("No access_token in response.")
                raise AccessDenied()
            # 2. THE KEY:
            # If it's GitHub (no id_token), bypass OIDC and use Odoo core
            if not id_token:
                params["access_token"] = access_token
                # By returning super()
                # we let base Odoo handle UserInfo validation
                return super().auth_oauth(provider, params)
        # 3. For everything else (OpenID)
        # let the chain continue
        return super().auth_oauth(provider, params)

    @api.model
    def _auth_oauth_validate(self, provider, access_token):
        validation = super()._auth_oauth_validate(provider, access_token)
        # If Odoo couldn't find an email, use the login/username
        if not validation.get("email") and validation.get("login"):
            validation["email"] = validation["login"]
        return validation
