# Copyright (C) 2020 GlodoUK <https://www.glodo.uk/>
# Copyright (C) 2010-2016, 2022-2024 XCG Consulting <https://xcg-consulting.fr/>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import werkzeug.utils

from odoo import http
from odoo.http import request

from odoo.addons.auth_oauth.controllers.main import OAuthLogin
from odoo.addons.web.controllers.utils import ensure_db


# ----------------------------------------------------------
# Controller
# ----------------------------------------------------------
class OAuthAutoredirectLogin(OAuthLogin):
    """OAuth controller with autoredirect added"""

    def list_providers_with_autoredirect(self):
        providers = self.list_providers()
        saml_providers = {
            search_read["id"]
            for search_read in request.env["auth.oauth.provider"]
            .sudo()
            .search_read([("autoredirect", "=", True)], ["id"])
        }
        return [provider for provider in providers if provider["id"] in saml_providers]

    def _oauth_autoredirect(self):
        # automatically redirect if any provider is set up to do that
        autoredirect_providers = self.list_providers_with_autoredirect()
        # do not redirect if asked too or if an error has been found
        disable_autoredirect = (
            "disable_autoredirect" in request.params or "error" in request.params
        )
        if autoredirect_providers and not disable_autoredirect:
            return werkzeug.utils.redirect(
                autoredirect_providers[0]["auth_link"],
                303,
            )
        return None

    @http.route()
    def web_client(self, s_action=None, **kw):
        if not request.session.uid:
            result = self._oauth_autoredirect()
            if result:
                return result
        return super().web_client(s_action, **kw)

    @http.route()
    def web_login(self, *args, **kw):
        ensure_db()
        # copied from super
        if (
            request.httprequest.method == "GET"
            and request.session.uid
            and request.params.get("redirect")
        ):
            # Redirect if already logged in and redirect param is present
            return request.redirect(request.params.get("redirect"))

        if request.httprequest.method == "GET":
            result = self._oauth_autoredirect()
            if result:
                return result

        return super().web_login(*args, **kw)
