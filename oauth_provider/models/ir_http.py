# Copyright 2022 Hunki Enterprises BV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import json
import oauthlib
from odoo import http, models
from werkzeug.exceptions import BadRequest, Unauthorized


class IrHttp(models.AbstractModel):
    _inherit = 'ir.http'

    @classmethod
    def _auth_method_oauth_provider(cls):
        """ Implement auth method 'oauth_provider' """
        rule, arguments = cls._find_handler(return_rule=True)
        request = oauthlib.common.Request(*cls._oauth_get_request_information())
        access_token = oauthlib.oauth2.rfc6749.tokens.get_token_from_header(request)
        token = http.request.env['ir.http']._oauth_check_access_token(access_token)
        if not token:
            raise Unauthorized(response=cls._oauth_json_response(
                data={'error': 'invalid_or_expired_token'}, status=401))
        scopes = rule.endpoint.routing.get("oauth_scopes", [])
        if set(scopes) - set(token.mapped("scope_ids.code")):
            raise BadRequest(response=cls._oauth_json_response(
                data={'error': 'invalid_scope'}, status=400))
        http.request.uid = token.user_id.id
        http.request.oauth_token = token

    @classmethod
    def _oauth_get_request_information(cls):
        """ Retrieve needed arguments for oauthlib methods """
        uri = http.request.httprequest.base_url
        http_method = http.request.httprequest.method
        body = oauthlib.common.urlencode(
            http.request.httprequest.values.items())
        headers = http.request.httprequest.headers

        return uri, http_method, body, headers

    @classmethod
    def _oauth_json_response(cls, data=None, status=200, headers=None):
        """ Returns a json response to the client """
        if headers is None:
            headers = {'Content-Type': 'application/json'}

        return http.Response(
            json.dumps(data), status=status, headers=headers)

    def _oauth_check_access_token(self, access_token):
        """ Check if the provided access token is valid """
        Token = self.env['oauth.provider.token'].sudo()
        token = Token.search([
            ('token', '=', access_token),
        ])
        if not token:
            return Token

        oauth2_server = token.client_id.get_oauth2_server()
        # Retrieve needed arguments for oauthlib methods
        uri, http_method, body, headers = self._oauth_get_request_information()

        # Validate request information
        valid, oauthlib_request = oauth2_server.verify_request(
            uri, http_method=http_method, body=body, headers=headers)

        if valid:
            return token

        return Token
