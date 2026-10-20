# Copyright 2021 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from urllib.parse import parse_qsl, urlparse

from odoo import http
from odoo.http import request

from odoo.addons.auth_oauth.controllers.main import OAuthLogin


class OAuthAutoLogin(OAuthLogin):
    def _autologin_disabled(self, redirect):
        url = urlparse(redirect)
        params = dict(parse_qsl(url.query, keep_blank_values=True))
        return "no_autologin" in params or "oauth_error" in params or "error" in params

    def _autologin_link(self):
        providers = [p for p in self.list_providers() if p.get("autologin")]
        if len(providers) == 1:
            return providers[0].get("auth_link")

    @http.route()
    def web_login(self, *args, **kw):
        # Odoo 18 uses deep links, so the full URL path is available to the server.
        # We can perform a server-side redirect if autologin is enabled.
        if request.httprequest.method == "GET" and not self._autologin_disabled(
            request.httprequest.url
        ):
            auth_link = self._autologin_link()
            if auth_link:
                return request.redirect(auth_link, 303, local=False)
        return super().web_login(*args, **kw)
