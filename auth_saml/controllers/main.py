# Copyright (C) 2020 GlodoUK <https://www.glodo.uk/>
# Copyright (C) 2010-2016, 2022-2023 XCG Consulting <https://xcg-consulting.fr/>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import functools
import json
import logging

import werkzeug.utils
from werkzeug.exceptions import BadRequest
from werkzeug.urls import url_quote_plus

from odoo import (
    SUPERUSER_ID,
    _,
    api,
    exceptions,
    http,
    models,
    modules,
)
from odoo.http import request
from odoo.tools.misc import clean_context

from odoo.addons.web.controllers.home import Home
from odoo.addons.web.controllers.utils import _get_login_redirect_url, ensure_db

_logger = logging.getLogger(__name__)


# ----------------------------------------------------------
# helpers
# ----------------------------------------------------------


def fragment_to_query_string(func):
    @functools.wraps(func)
    def wrapper(self, **kw):
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
        return func(self, **kw)

    return wrapper


# ----------------------------------------------------------
# Controller
# ----------------------------------------------------------


class SAMLLogin(Home):
    # Disable pylint self use as the method is meant to be reused in other modules
    def _list_saml_providers_domain(self):  # pylint: disable=no-self-use
        return []

    def list_saml_providers(self, with_autoredirect: bool = False) -> models.Model:
        """Return available providers

        :param with_autoredirect: True to only list providers with automatic redirection
        :return: a recordset of providers
        """
        domain = self._list_saml_providers_domain()
        if with_autoredirect:
            domain.append(("autoredirect", "=", True))
        providers = request.env["auth.saml.provider"].sudo().search_read(domain)
        for provider in providers:
            provider["auth_link"] = self._auth_saml_request_link(provider)
        return providers

    def _saml_autoredirect(self):
        # automatically redirect if any provider is set up to do that
        autoredirect_providers = self.list_saml_providers(True)
        # do not redirect if asked too or if a SAML error has been found
        disable_autoredirect = (
            "disable_autoredirect" in request.params or "saml_error" in request.params
        )
        if autoredirect_providers and not disable_autoredirect:
            return werkzeug.utils.redirect(
                self._auth_saml_request_link(autoredirect_providers[0]),
                303,
            )
        return None

    def _auth_saml_request_link(self, provider: models.Model):
        """Return the auth request link for the provided provider"""
        params = {
            "pid": provider["id"],
        }
        redirect = request.params.get("redirect")
        if redirect:
            params["redirect"] = redirect
        return f"/auth_saml/get_auth_request?{werkzeug.urls.url_encode(params)}"

    @http.route()
    def web_client(self, s_action=None, **kw):
        ensure_db()
        if not request.session.uid:
            result = self._saml_autoredirect()
            if result:
                return result
        return super().web_client(s_action, **kw)

    @http.route()
    def web_login(self, *args, **kw):
        ensure_db()
        if (
            request.httprequest.method == "GET"
            and request.session.uid
            and request.params.get("redirect")
        ):
            # Redirect if already logged in and redirect param is present
            return request.redirect(request.params.get("redirect"))

        if request.httprequest.method == "GET":
            result = self._saml_autoredirect()
            if result:
                return result

        providers = self.list_saml_providers()

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

            response.qcontext["saml_providers"] = providers

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

    @http.route("/auth_saml/get_auth_request", type="http", auth="none", readonly=False)
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

    def _extract_user_info_from_saml_response(self, provider_id, saml_response, base_url):
        """Extract user information from SAML response for user creation"""
        try:
            # Simple approach: just extract the NameID which we can see in the logs
            # From the logs we can see: Subject NameID: bringsvor@bringsvor.com
            
            # For now, let's use a simple regex to extract the email from the SAML response
            import re
            import base64
            
            # Decode the SAML response to look for the NameID
            try:
                decoded_response = base64.b64decode(saml_response).decode('utf-8')
                
                # Look for NameID pattern
                nameid_pattern = r'<[^>]*NameID[^>]*>([^<]+)</[^>]*NameID>'
                nameid_match = re.search(nameid_pattern, decoded_response)
                
                if nameid_match:
                    nameid_value = nameid_match.group(1).strip()
                    user_info = {
                        'login': nameid_value,
                        'email': nameid_value if '@' in nameid_value else '',
                        'name': nameid_value.split('@')[0] if '@' in nameid_value else nameid_value
                    }
                    _logger.info("SAML2: Extracted user info from NameID: %s", user_info)
                    return user_info
                
            except Exception as decode_error:
                _logger.warning("SAML2: Could not decode SAML response: %s", str(decode_error))
            
            # Fallback: return empty info
            _logger.warning("SAML2: Could not extract user info from SAML response")
            return {}
            
        except Exception as e:
            _logger.exception("Failed to extract user info from SAML response: %s", str(e))
            return {}

    @http.route(
        "/auth_saml/signin", type="http", auth="none", csrf=False, readonly=False
    )
    @fragment_to_query_string
    def signin(self, **kw):
        """
        Client obtained a saml token and passed it back
        to us... we need to validate it
        """
        saml_response = kw.get("SAMLResponse")

        if not kw.get("RelayState"):
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
        if not http.db_filter([dbname]):
            return BadRequest()
        ensure_db(db=dbname)

        request.update_context(**clean_context(state.get("c", {})))
        try:
            credentials = (
                request.env["res.users"]
                .with_user(SUPERUSER_ID)
                .auth_saml(
                    provider,
                    saml_response,
                    request.httprequest.url_root.rstrip("/"),
                )
            )
            action = state.get("a")
            menu = state.get("m")
            redirect = (
                werkzeug.urls.url_unquote_plus(state["r"]) if state.get("r") else False
            )
            url = "/web"
            if redirect:
                url = redirect
            elif action:
                url = f"/#action={action}"
            elif menu:
                url = f"/#menu_id={menu}"

            credentials_dict = {
                "login": credentials[1],
                "token": credentials[2],
                "type": "saml_token",
            }
            auth_info = request.session.authenticate(dbname, credentials_dict)
            resp = request.redirect(_get_login_redirect_url(auth_info["uid"], url), 303)
            resp.autocorrect_location_header = False
            return resp

        except exceptions.AccessDenied:
            # saml credentials not valid, user could be on a temporary session
            # Try to create user if it doesn't exist
            try:
                # First, let's see what the validation actually returns
                provider_obj = request.env["auth.saml.provider"].sudo().browse(provider)
                validation = provider_obj._validate_auth_response(saml_response, request.httprequest.url_root.rstrip("/"))
                _logger.info("SAML2: Validation result: %s", validation)
                if validation.get("user_id"):
                    _logger.info("SAML2: Expected SAML UID from validation: %s", validation["user_id"])
                
                user_info = self._extract_user_info_from_saml_response(
                    provider, saml_response, request.httprequest.url_root.rstrip("/")
                )
                
                if user_info and user_info.get('login'):
                    # Check if user already exists
                    existing_user = request.env['res.users'].sudo().search([
                        ('login', '=', user_info['login'])
                    ], limit=1)
                    
                    if not existing_user:
                        # Create new user in activated state (no email verification needed)
                        company = request.env['res.company'].sudo().search([], limit=1)
                        if not company:
                            raise Exception("No company found in database")
                        
                        # Create user with context that bypasses signup workflow
                        new_user = request.env['res.users'].with_user(1).sudo().with_context(
                            no_reset_password=True,
                            mail_create_nosubscribe=True,
                            mail_create_nolog=True
                        ).create({
                            'name': user_info.get('name', user_info['login']),
                            'login': user_info['login'],
                            'email': user_info.get('email', user_info['login']),
                            'company_id': company.id,
                            'company_ids': [(6, 0, [company.id])],
                            'groups_id': [(6, 0, [
                                request.env.ref('base.group_user').id,
                            ])],
                            'active': True,
                        })
                        
                        _logger.info("SAML2: Created activated user with company: %s, allowed companies: %s", 
                                   company.name, new_user.company_ids.mapped('name'))
                        
                        # Create the SAML linking record - this is crucial!
                        saml_uid = validation.get("user_id", user_info['login'])  # Use validation user_id or fallback to email
                        request.env['res.users.saml'].sudo().create({
                            'user_id': new_user.id,
                            'saml_provider_id': provider,
                            'saml_uid': saml_uid,
                        })
                        
                        _logger.info("SAML2: Created new user %s with SAML linking record, SAML UID: %s", new_user.login, saml_uid)
                        
                        # Commit the user creation immediately so it's available for authentication
                        request.env.cr.commit()
                        _logger.info("SAML2: User creation committed to database")
                    
                    else:
                        # User exists, check if SAML linking record exists
                        saml_link = request.env['res.users.saml'].sudo().search([
                            ('user_id', '=', existing_user.id),
                            ('saml_provider_id', '=', provider)
                        ], limit=1)
                        
                        # Always recreate the SAML linking record with correct saml_uid
                        if saml_link:
                            saml_link.unlink()  # Delete existing wrong record
                            _logger.info("SAML2: Deleted existing SAML linking record for user %s", existing_user.login)
                        
                        # Create new SAML linking record with correct saml_uid
                        saml_uid = validation.get("user_id", user_info['login'])  # Use validation user_id or fallback to email
                        request.env['res.users.saml'].sudo().create({
                            'user_id': existing_user.id,
                            'saml_provider_id': provider,
                            'saml_uid': saml_uid,
                        })
                        _logger.info("SAML2: Created SAML linking record for existing user %s with SAML UID: %s", existing_user.login, saml_uid)
                    
                    # Try authentication again now that SAML linking record exists
                    try:
                        credentials = (
                            request.env["res.users"]
                            .with_user(SUPERUSER_ID)
                            .auth_saml(
                                provider,
                                saml_response,
                                request.httprequest.url_root.rstrip("/"),
                            )
                        )
                        
                        action = state.get("a")
                        menu = state.get("m")
                        redirect = (
                            werkzeug.urls.url_unquote_plus(state["r"]) if state.get("r") else False
                        )
                        url = "/web"
                        if redirect:
                            url = redirect
                        elif action:
                            url = f"/#action={action}"
                        elif menu:
                            url = f"/#menu_id={menu}"
                        
                        credentials_dict = {
                            "login": credentials[1],
                            "token": credentials[2],
                            "type": "saml_token",
                        }
                        auth_info = request.session.authenticate(dbname, credentials_dict)
                        resp = request.redirect(_get_login_redirect_url(auth_info["uid"], url), 303)
                        resp.autocorrect_location_header = False
                        return resp
                        
                    except exceptions.AccessDenied:
                        _logger.info("SAML2: Authentication still failed even after creating SAML linking record")
                
            except Exception as create_error:
                _logger.exception("SAML2: Failed to create user - %s", str(create_error))
            
            # Fall back to original behavior if user creation fails
            _logger.info("SAML2: access denied")
            url = "/web/login?saml_error=expired"
            redirect = werkzeug.utils.redirect(url, 303)
            redirect.autocorrect_location_header = False
            return redirect

        except Exception as e:
            # signup error
            _logger.exception("SAML2: failure - %s", str(e))
            url = "/web/login?saml_error=access-denied"

        redirect = request.redirect(url, 303)
        redirect.autocorrect_location_header = False
        return redirect

    @http.route(
        "/auth_saml/metadata", type="http", auth="none", csrf=False, readonly=False
    )
    def saml_metadata(self, **kw):
        provider = kw.get("p")
        dbname = kw.get("d")
        valid = kw.get("valid", None)

        if not dbname or not provider:
            _logger.debug("Metadata page asked without database name or provider id")
            raise request.not_found(_("Missing parameters"))

        provider = int(provider)

        with modules.registry.Registry(dbname).cursor() as cr:
            env = api.Environment(cr, SUPERUSER_ID, {})
            client = env["auth.saml.provider"].sudo().browse(provider)
            if not client.exists():
                raise request.not_found(_("Unknown provider"))

            return request.make_response(
                client._metadata_string(
                    valid, request.httprequest.url_root.rstrip("/")
                ),
                [("Content-Type", "text/xml")],
            )
