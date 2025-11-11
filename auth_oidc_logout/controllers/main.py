# Copyright 2016 ICTSTUDIO <http://www.ictstudio.eu>
# Copyright 2021 ACSONE SA/NV <https://acsone.eu>
# License: AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
from urllib.parse import parse_qs, urljoin, urlparse

from werkzeug.urls import url_encode

from odoo import http
from odoo.http import request

from odoo.addons.web.controllers.session import Session


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
                logout_url = components._replace(query=url_encode(params)).geturl()
                # Override the session logout to allow a non local redirect
                request.session.logout(keep_db=True)
                return request.env["ir.http"]._redirect(logout_url, 303)
        # User has no account with any provider or no logout URL is configured for the provider
        return super().logout(redirect=redirect)
