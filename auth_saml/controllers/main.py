# Copyright (C) 2010-2016 XCG Consulting <http://odoo.consulting>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import functools
import logging

import json as simplejson
import werkzeug.utils

import odoo
from odoo import api, _, http, SUPERUSER_ID
from odoo.http import request
from odoo import registry as registry_get
from odoo.addons.web.controllers.main import set_cookie_and_redirect
from odoo.addons.web.controllers.main import ensure_db
from odoo.addons.web.controllers.main import login_and_redirect
from odoo.addons.web.controllers.main import Home


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

    def list_providers(self):
        providers = request.env['auth.saml.provider'].sudo().search_read([])
        for provider in providers:
            # Compatibility with auth_oauth/controllers/main.py in order to
            # avoid KeyError rendering template_auth_oauth_providers
            provider.setdefault('auth_link', "")
        return providers

    @http.route()
    def web_login(self, *args, **kw):
        ensure_db()
        if (
            request.httprequest.method == 'GET' and
            request.session.uid and
            request.params.get('redirect')
        ):

            # Redirect if already logged in and redirect param is present
            return http.redirect_with_hash(request.params.get('redirect'))

        providers = self.list_providers()

        response = super().web_login(*args, **kw)
        if response.is_qweb:
            error = request.params.get('saml_error')
            if error == 'no-signup':
                error = _("Sign up is not allowed on this database.")
            elif error == 'access-denied':
                error = _("Access Denied")
            elif error == 'expired':
                error = _(
                    "You do not have access to this database or your "
                    "invitation has expired. Please ask for an invitation "
                    "and be sure to follow the link in your invitation email."
                )
            else:
                error = None

            response.qcontext['providers'] = providers

            if error:
                response.qcontext['error'] = error

        return response


class AuthSAMLController(http.Controller):

    def get_state(self, provider_id):
        """Compute a state to be sent to the IDP so it can forward it back to
        us.

        :rtype: Dictionary.
        """

        redirect = request.params.get('redirect') or 'web'
        if not redirect.startswith(('//', 'http://', 'https://')):
            redirect = '%s%s' % (
                request.httprequest.url_root,
                redirect[1:] if redirect[0] == '/' else redirect
            )

        state = {
            "d": request.session.db,
            "p": provider_id,
            "r": werkzeug.url_quote_plus(redirect),
        }
        return state

    @http.route('/auth_saml/get_auth_request', type='http', auth='none')
    def get_auth_request(self, pid):
        provider_id = int(pid)

        auth_request = None

        # store a RelayState on the request to our IDP so that the IDP
        # can send us back this info alongside the obtained token
        state = self.get_state(provider_id)

        try:
            Provider = request.env[
                'auth.saml.provider'].sudo()
            provider = Provider.browse(provider_id)
            auth_request = provider._get_auth_request(state)

        except Exception:
            _logger.exception("SAML2 failure")

        # TODO: handle case when auth_request comes back as None

        redirect = werkzeug.utils.redirect(auth_request, 303)
        redirect.autocorrect_location_header = True
        return redirect

    @http.route('/auth_saml/signin', type='http', auth='none', csrf=False)
    @fragment_to_query_string
    def signin(self, req, **kw):
        """client obtained a saml token and passed it back
        to us... we need to validate it
        """
        saml_response = kw.get('SAMLResponse')

        if kw.get('RelayState') is None:
            # here we are in front of a client that went through
            # some routes that "lost" its relaystate... this can happen
            # if the client visited his IDP and successfully logged in
            # then the IDP gave him a portal with his available applications
            # but the provided link does not include the necessary relaystate
            url = "/?type=signup"
            redirect = werkzeug.utils.redirect(url, 303)
            redirect.autocorrect_location_header = True
            return redirect

        state = simplejson.loads(kw['RelayState'])
        provider = state['p']
        dbname = state['d']
        context = state.get('c', {})
        registry = registry_get(dbname)
        with registry.cursor() as cr:
            try:
                env = api.Environment(cr, SUPERUSER_ID, context)
                credentials = env['res.users'].sudo().auth_saml(
                    provider, saml_response
                )
                action = state.get('a')
                menu = state.get('m')
                url = '/'
                if action:
                    url = '/#action=%s' % action
                elif menu:
                    url = '/#menu_id=%s' % menu
                # otherwise login_and_redirect uses an env different from this
                # "env" used here, where "saml_access_token" is not up to date
                cr.commit()
                return login_and_redirect(*credentials, redirect_url=url)

            except AttributeError as e:
                # auth_signup is not installed
                _logger.error("auth_signup not installed on database "
                              "saml sign up cancelled.")
                url = "/#action=login&saml_error=no-signup"

            except odoo.exceptions.AccessDenied:
                # saml credentials not valid,
                # user could be on a temporary session
                _logger.info('SAML2: access denied, redirect to main page '
                             'in case a valid session exists, '
                             'without setting cookies')

                url = "/#action=login&saml_error=expired"
                redirect = werkzeug.utils.redirect(url, 303)
                redirect.autocorrect_location_header = False
                return redirect

            except Exception:
                # signup error
                _logger.exception("SAML2: failure")
                url = "/#action=login&saml_error=access-denied"

        return set_cookie_and_redirect(url)
