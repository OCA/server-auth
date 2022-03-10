# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

import json

import uuid

import werkzeug.urls
import werkzeug.utils

from odoo.http import request

from odoo.addons.auth_oauth.controllers.main import OAuthLogin


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
