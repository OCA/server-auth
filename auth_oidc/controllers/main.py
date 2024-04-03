# Copyright 2016 ICTSTUDIO <http://www.ictstudio.eu>
# Copyright 2021 ACSONE SA/NV <https://acsone.eu>
# License: AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

import base64
import hashlib
import logging
import secrets

from werkzeug.urls import url_decode, url_encode

from odoo.addons.auth_oauth.controllers.main import OAuthLogin

_logger = logging.getLogger(__name__)


class OpenIDLogin(OAuthLogin):
    def list_providers(self):
        providers = super().list_providers()
        for provider in providers:
            flow = provider.get("flow")
            if flow in ("id_token", "id_token_code"):
                params = url_decode(provider["auth_link"].split("?")[-1])
                # nonce
                params["nonce"] = secrets.token_urlsafe()
                # response_type
                if flow == "id_token":
                    # https://openid.net/specs/openid-connect-core-1_0.html
                    # #ImplicitAuthRequest
                    params["response_type"] = "id_token token"
                elif flow == "id_token_code":
                    # https://openid.net/specs/openid-connect-core-1_0.html#AuthRequest
                    params["response_type"] = "code"
                # PKCE (https://tools.ietf.org/html/rfc7636)
                code_verifier = provider["code_verifier"]
                code_challenge = base64.urlsafe_b64encode(
                    hashlib.sha256(code_verifier.encode("ascii")).digest()
                ).rstrip(b"=")
                params["code_challenge"] = code_challenge
                params["code_challenge_method"] = "S256"
                # scope
                if provider.get("scope"):
                    if "openid" not in provider["scope"].split():
                        _logger.error("openid connect scope must contain 'openid'")
                    params["scope"] = provider["scope"]
                # auth link that the user will click
                provider["auth_link"] = "{}?{}".format(
                    provider["auth_endpoint"], url_encode(params)
                )
        return providers
