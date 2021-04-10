# Copyright 2016 ICTSTUDIO <http://www.ictstudio.eu>
# Copyright 2021 ACSONE SA/NV <https://acsone.eu>
# License: AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

import logging

import requests

from odoo import api, models
from odoo.exceptions import AccessDenied
from odoo.http import request

_logger = logging.getLogger(__name__)


class ResUsers(models.Model):
    _inherit = "res.users"

    @api.model
    def auth_oauth(self, provider, params):
        oauth_provider = self.env["auth.oauth.provider"].browse(provider)
        if oauth_provider.flow not in ("id_token", "id_token_code"):
            return super(ResUsers, self).auth_oauth(provider, params)

        if oauth_provider.flow == "id_token":
            # https://openid.net/specs/openid-connect-core-1_0.html#ImplicitAuthResponse
            access_token = params.get("access_token")
            id_token = params.get("id_token")
        elif oauth_provider.flow == "id_token_code":
            # https://openid.net/specs/openid-connect-core-1_0.html#AuthResponse
            code = params.get("code")
            # https://openid.net/specs/openid-connect-core-1_0.html#TokenRequest
            auth = None
            if oauth_provider.client_secret:
                auth = (oauth_provider.client_id, oauth_provider.client_secret)
            response = requests.post(
                oauth_provider.token_endpoint,
                data=dict(
                    client_id=oauth_provider.client_id,
                    grant_type="authorization_code",
                    code=code,
                    code_verifier=oauth_provider.code_verifier,  # PKCE
                    redirect_uri=request.httprequest.url_root + "auth_oauth/signin",
                ),
                auth=auth,
            )
            response.raise_for_status()
            response_json = response.json()
            # https://openid.net/specs/openid-connect-core-1_0.html#TokenResponse
            access_token = response_json.get("access_token")
            id_token = response_json.get("id_token")
        if not access_token:
            _logger.error("No access_token in response.")
            raise AccessDenied()
        if not id_token:
            _logger.error("No id_token in response.")
            raise AccessDenied()
        validation = oauth_provider._parse_id_token(id_token, access_token)
        # required check
        if not validation.get("user_id"):
            _logger.error("user_id claim not found in id_token (after mapping).")
            raise AccessDenied()
        # retrieve and sign in user
        params["access_token"] = access_token
        login = self._auth_oauth_signin(provider, validation, params)
        if not login:
            raise AccessDenied()
        # return user credentials
        return (self.env.cr.dbname, login, access_token)
