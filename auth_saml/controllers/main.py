# Copyright (C) 2020 GlodoUK <https://www.glodo.uk/>
# Copyright (C) 2010-2016 XCG Consulting <http://odoo.consulting>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import functools
import json
import logging

import werkzeug.utils
from werkzeug.urls import url_quote_plus

import odoo
from odoo import SUPERUSER_ID, _, api, http, registry as registry_get
from odoo.http import request

from odoo.addons.web.controllers.main import (
    Home,
    ensure_db,
    login_and_redirect,
    set_cookie_and_redirect,
)

_logger = logging.getLogger(__name__)


# ----------------------------------------------------------
# helpers
# ----------------------------------------------------------


def fragment_to_query_string(func):
    @functools.wraps(func)
    def wrapper(self, req, **kw):
        if not kw:
            return """<html><head><script>
                var l = window.location;
                var q = l.hash.substring(1);
                var r = '/' + l.search;
                if(q.length !== 0) {
                    var s = l.search ? (l.search === '?' ? '' : '&') : '?';
                    r = l.pathname + l.search + s + q;
                }
                window.location = r;
            </script></head><body></body></html>"""
        return func(self, req, **kw)

    return wrapper


# ----------------------------------------------------------
# Controller
# ----------------------------------------------------------


class SAMLLogin(Home):
    def _list_saml_providers_domain(self):
        return []

    def list_providers(self):
        providers = (
            request.env["auth.saml.provider"]
            .sudo()
            .search_read(self._list_saml_providers_domain())
        )

        for provider in providers:
            # Compatibility with auth_oauth/controllers/main.py in order to
            # avoid KeyError rendering template_auth_oauth_providers
            provider.setdefault("auth_link", "")
        return providers

    @http.route()
    def web_login(self, *args, **kw):
        ensure_db()
        if (
            request.httprequest.method == "GET"
            and request.session.uid
            and request.params.get("redirect")
        ):

            # Redirect if already logged in and redirect param is present
            return http.redirect_with_hash(request.params.get("redirect"))

        providers = self.list_providers()

        response = super().web_login(*args, **kw)
        if response.is_qweb:
            error = request.params.get("saml_error")
            if error == "no-signup":
                error = _("Sign up is not allowed on this database.")
            elif error == "access-denied":
                error = _("Access Denied")
            elif error == "expired":
                error = _(
                    "You do not have access to this database. Please contact"
                    " support."
                )
            else:
                error = None

            response.qcontext["providers"] = providers

            if error:
                response.qcontext["error"] = error

        return response


class AuthSAMLController(http.Controller):
    def _get_saml_extra_relaystate(self):
        """
        Compute any additional extra state to be sent to the IDP so it can
        forward it back to us. This is called RelayState.

        The provider will automatically set things like the dbname, provider
        id, etc.
        """

        redirect = request.params.get("redirect") or "web"
        if not redirect.startswith(("//", "http://", "https://")):
            redirect = "{}{}".format(
                request.httprequest.url_root,
                redirect[1:] if redirect[0] == "/" else redirect,
            )

        state = {
            "r": url_quote_plus(redirect),
        }
        return state

    @http.route("/auth_saml/get_auth_request", type="http", auth="none")
    def get_auth_request(self, pid):
        provider_id = int(pid)

        provider = request.env["auth.saml.provider"].sudo().browse(provider_id)
        redirect_url = provider._get_auth_request(
            self._get_saml_extra_relaystate(), request.httprequest.url_root.rstrip("/")
        )
        if not redirect_url:
            raise Exception(
                "Failed to get auth request from provider. "
                "Either misconfigured SAML provider or unknown provider."
            )

        redirect = werkzeug.utils.redirect(redirect_url, 303)
        redirect.autocorrect_location_header = True
        return redirect

    @http.route("/auth_saml/signin", type="http", auth="none", csrf=False)
    @fragment_to_query_string
    def signin(self, req, **kw):
        """
        Client obtained a saml token and passed it back
        to us... we need to validate it
        """
        saml_response = kw.get("SAMLResponse")

        if kw.get("RelayState") is None:
            # here we are in front of a client that went through
            # some routes that "lost" its relaystate... this can happen
            # if the client visited his IDP and successfully logged in
            # then the IDP gave him a portal with his available applications
            # but the provided link does not include the necessary relaystate
            url = "/?type=signup"
            redirect = werkzeug.utils.redirect(url, 303)
            redirect.autocorrect_location_header = True
            return redirect

        state = json.loads(kw["RelayState"])
        provider = state["p"]
        dbname = state["d"]
        context = state.get("c", {})
        registry = registry_get(dbname)

        with registry.cursor() as cr:
            try:
                env = api.Environment(cr, SUPERUSER_ID, context)
                credentials = (
                    env["res.users"]
                    .sudo()
                    .auth_saml(
                        provider,
                        saml_response,
                        request.httprequest.url_root.rstrip("/"),
                    )
                )
                action = state.get("a")
                menu = state.get("m")
                url = "/"
                if action:
                    url = "/#action=%s" % action
                elif menu:
                    url = "/#menu_id=%s" % menu
                return login_and_redirect(*credentials, redirect_url=url)

            except odoo.exceptions.AccessDenied:
                # saml credentials not valid,
                # user could be on a temporary session
                _logger.info("SAML2: access denied")

                url = "/web/login?saml_error=expired"
                redirect = werkzeug.utils.redirect(url, 303)
                redirect.autocorrect_location_header = False
                return redirect

            except Exception as e:
                # signup error
                _logger.exception("SAML2: failure - %s", str(e))
                url = "/web/login?saml_error=access-denied"

        return set_cookie_and_redirect(url)

    @http.route("/auth_saml/metadata", type="http", auth="none", csrf=False)
    def saml_metadata(self, req, **kw):
        provider = kw.get("p")
        dbname = kw.get("d")
        valid = kw.get("valid", None)

        if not dbname or not provider:
            raise Exception("Missing parameters")

        provider = int(provider)

        registry = registry_get(dbname)

        with registry.cursor() as cr:
            env = api.Environment(cr, SUPERUSER_ID, {})
            client = env["auth.saml.provider"].sudo().browse(provider)

            return request.make_response(
                client._metadata_string(
                    valid, request.httprequest.url_root.rstrip("/")
                ),
                [("Content-Type", "text/xml")],
            )
