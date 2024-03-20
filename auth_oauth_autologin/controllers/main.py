# Copyright 2021 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import werkzeug

from odoo import http

from odoo.addons.auth_oauth.controllers.main import OAuthLogin


class OAuthAutoLogin(OAuthLogin):
    def _autologin_disabled(self):
        return (
            "no_autologin" in http.request.params
            or "oauth_error" in http.request.params
            or "error" in http.request.params
        )

    def _autologin_link(self):
        providers = [p for p in self.list_providers() if p.get("autologin")]
        if len(providers) == 1:
            return providers[0].get("auth_link")

    @http.route()
    def web_login(self, *args, **kw):
        response = super().web_login(*args, **kw)
        if not response.is_qweb:
            # presumably a redirect already
            return response
        if self._autologin_disabled():
            return response
        auth_link = self._autologin_link()
        if not auth_link:
            return response
        return werkzeug.utils.redirect(auth_link, 303)
