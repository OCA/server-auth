# Copyright 2016 ICTSTUDIO <http://www.ictstudio.eu>
# Copyright 2021 ACSONE SA/NV <https://acsone.eu>
# License: AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

import logging
import secrets

import werkzeug.utils

from odoo.addons.auth_oauth.controllers.main import OAuthLogin

_logger = logging.getLogger(__name__)


class OpenIDLogin(OAuthLogin):
    def list_providers(self):
        providers = super(OpenIDLogin, self).list_providers()
        for provider in providers:
            flow = provider.get("flow")
            if flow in ("id_token", "id_token_code"):
                params = werkzeug.url_decode(provider["auth_link"].split("?")[-1])
                params["nonce"] = secrets.token_urlsafe()
                if flow == "id_token":
                    # https://openid.net/specs/openid-connect-core-1_0.html
                    # #ImplicitAuthRequest
                    params["response_type"] = "id_token token"
                elif flow == "id_token_code":
                    # https://openid.net/specs/openid-connect-core-1_0.html#AuthRequest
                    params["response_type"] = "code"
                if provider.get("scope"):
                    if "openid" not in provider["scope"].split():
                        _logger.error("openid connect scope must contain 'openid'")
                    params["scope"] = provider["scope"]
                provider["auth_link"] = "{}?{}".format(
                    provider["auth_endpoint"], werkzeug.url_encode(params)
                )
        return providers
