# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

import json
from odoo import http
import uuid

import werkzeug.urls
import werkzeug.utils

from odoo.http import request

from odoo.addons.auth_oauth.controllers.main import OAuthLogin
from odoo.addons.web.controllers.main import Session


_logger = logging.getLogger(__name__)


# ----------------------------------------------------------
# Controller
# ----------------------------------------------------------
class OAuthLoginKeycloak(OAuthLogin):
    def list_providers(self):
        try:
            providers = request.env['auth.oauth.provider'].sudo().search_read(
                [('enabled', '=', True)]
            )
        except Exception:
            providers = []
        for provider in providers:
            return_url = request.httprequest.url_root + 'auth_oauth/signin'
            state = self.get_state(provider)
            params = dict(
                response_type='token',
                client_id=provider['client_id'],
                redirect_uri=return_url,
                scope=provider['scope'],
                state=json.dumps(state),
                # a nonce is mandatory for keycloak
                # otherwise it returns a Bad Request code
                # see https://tools.ietf.org/html/rfc6819
                nonce=str(uuid.uuid4()),
            )
            provider['auth_link'] = "%s?%s" % (
                provider['auth_endpoint'],
                werkzeug.url_encode(params)
            )
        return providers




class SessionAutoLogout(Session):

    @http.route('/web/session/logout', type='http', auth="none")
    def logout(self, redirect='/web'):
        # request.session.logout(keep_db=True)
        # return werkzeug.utils.redirect('/logout', 303)

        redirect = '/logout'
        return super(SessionAutoLogout, self).logout(redirect=redirect)
