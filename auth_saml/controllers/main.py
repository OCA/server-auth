# Copyright (C) 2010-2019 XCG Consulting <http://odoo.consulting>
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

    def list_providers(self, with_autoredirect=False):
        try:
            domain = [('enabled', '=', True)]
            if with_autoredirect:
                domain.append(('autoredirect', '=', True))
            providers = request.env['auth.saml.provider'].sudo().search_read(
                domain)
        except Exception as e:
            _logger.exception("SAML2: %s" % str(e))
            providers = []

        return providers

    def _saml_autoredirect(self):
        # automatically redirect if any provider is set up to do that
        autoredirect_providers = self.list_providers(True)
        # do not redirect if asked too or if a SAML error has been found
        disable_autoredirect = (
            'disable_autoredirect' in request.params or
            'error' in request.params)
        if autoredirect_providers and not disable_autoredirect:
            return werkzeug.utils.redirect(
                '/auth_saml/get_auth_request?pid=%d' %
                autoredirect_providers[0]['id'],
                303)

    @http.route()
    def web_client(self, s_action=None, **kw):
        ensure_db()
        if not request.session.uid:
            result = self._saml_autoredirect()
            if result:
                return result
            else:
                return super(SAMLLogin, self).web_client(s_action, **kw)
        return super(SAMLLogin, self).web_client(s_action, **kw)

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

        if request.httprequest.method == 'GET':
            result = self._saml_autoredirect()
            if result:
                return result

        providers = self.list_providers()

        response = super(SAMLLogin, self).web_login(*args, **kw)
        if response.is_qweb:
            errorcode = request.params.get('error')
            if errorcode == 'saml1':
            error = None
                error = _("Sign up is not allowed on this database.")
            elif errorcode == 'saml2':
                error = _("Access Denied")
            elif errorcode == 'saml3':
                error = _(
                    "You do not have access to this database or your "
                    "invitation has expired. Please ask for an invitation "
                    "and be sure to follow the link in your invitation email."
                )

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
        """state is the JSONified state object and we need to pass
        it inside our request as the RelayState argument
        """

        provider_id = int(pid)

        auth_request = None

        # store a RelayState on the request to our IDP so that the IDP
        # can send us back this info alongside the obtained token
        state = self.get_state(provider_id)

        try:
            auth_request = request.env[
                'auth.saml.provider'].sudo().browse(
                    provider_id)._get_auth_request(state)

        except Exception as e:
            _logger.exception("SAML2: %s" % str(e))

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
        saml_response = kw.get('SAMLResponse', None)

        if kw.get('RelayState', None) is None:
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
                cr.commit()
                action = state.get('a')
                menu = state.get('m')
                url = '/'
                # XXX this probably should be changed for odoo 11
                if action:
                    url = '/#action=%s' % action
                elif menu:
                    url = '/#menu_id=%s' % menu
                return login_and_redirect(*credentials, redirect_url=url)

            except AttributeError as e:
                # auth_signup is not installed
                _logger.error("auth_signup not installed on database "
                              "saml sign up cancelled.")
                url = "/web/login?error=saml1"

            except odoo.exceptions.AccessDenied:
                # saml credentials not valid,
                # user could be on a temporary session
                _logger.info('SAML2: access denied, redirect to main page '
                             'in case a valid session exists, '
                             'without setting cookies')

                url = "/web/login?error=saml3"
                redirect = werkzeug.utils.redirect(url, 303)
                redirect.autocorrect_location_header = False
                return redirect

            except Exception as e:
                # signup error
                _logger.exception("SAML2: %s" % str(e))
                url = "//web/login?error=saml2"

        return set_cookie_and_redirect(url)
