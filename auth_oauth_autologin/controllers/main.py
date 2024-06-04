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

    @http.route(
        "/auth/auto_login_redirect_link",
        type="json",
        auth="none",
    )
    def auto_login_redirect_link(self, *args, **kwargs):
        redirect = kwargs.get("redirect")
        if self._autologin_disabled(redirect):
            return False
        request.params["redirect"] = redirect
        auth_link = self._autologin_link()
        return auth_link
