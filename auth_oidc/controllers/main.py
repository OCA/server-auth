# Copyright 2016 ICTSTUDIO <http://www.ictstudio.eu>
# Copyright 2021 ACSONE SA/NV <https://acsone.eu>
# License: AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

import base64
import hashlib
import logging
import secrets
from urllib.parse import parse_qs, urljoin, urlparse

from werkzeug.urls import url_decode, url_encode

from odoo import http
from odoo.http import request

from odoo.addons.auth_oauth.controllers.main import OAuthLogin
from odoo.addons.web.controllers.main import Session

_logger = logging.getLogger(__name__)


class OpenIDLogin(OAuthLogin):
    def list_providers(self):
        providers = super(OpenIDLogin, self).list_providers()
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


class OpenIDLogout(Session):
    @http.route("/web/session/logout", type="http", auth="none")
    def logout(self, redirect="/web/login"):
        # https://openid.net/specs/openid-connect-rpinitiated-1_0.html#RPLogout
        user = request.env["res.users"].sudo().browse(request.session.uid)
        if user.oauth_provider_id.id:
            provider = (
                request.env["auth.oauth.provider"]
                .sudo()
                .browse(user.oauth_provider_id.id)
            )
            if provider.end_session_endpoint:
                redirect_url = urljoin(request.httprequest.url_root, redirect)
                components = urlparse(provider.end_session_endpoint)
                params = parse_qs(components.query)
                params["client_id"] = provider.client_id
                params["post_logout_redirect_uri"] = redirect_url
                if provider.skip_logout_confirmation and user.oauth_id_token:
                    params["id_token_hint"] = user.oauth_id_token
                logout_url = components._replace(query=url_encode(params)).geturl()
                return super().logout(redirect=logout_url)
        # User has no account with any provider or no logout URL is configured for the provider
        return super().logout(redirect=redirect)
