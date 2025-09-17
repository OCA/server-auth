# Copyright 2016 SYLEAM
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
import logging
from datetime import datetime

import werkzeug.utils
import werkzeug.wrappers

from odoo import http

from odoo.addons.web.controllers.utils import ensure_db

_logger = logging.getLogger(__name__)

try:
    import oauthlib
    from oauthlib import oauth2
except ImportError:
    _logger.debug("Cannot `import oauthlib`.")


class OAuth2ProviderController(http.Controller):
    def _get_request_information(self):
        return http.request.env["ir.http"]._oauth_get_request_information()

    def _check_access_token(self, access_token):
        return http.request.env["ir.http"]._oauth_check_access_token(access_token)

    def _json_response(self, data=None, status=200, headers=None):
        return http.request.env["ir.http"]._oauth_json_response(
            data=data, status=status, headers=headers
        )

    @http.route(
        "/oauth2/authorize", type="http", auth="user", methods=["GET"], website=True
    )
    def authorize(
        self,
        client_id=None,
        response_type=None,
        redirect_uri=None,
        scope=None,
        state=None,
        *args,
        **kwargs,
    ):
        """Check client's request, and display an authorization page to the user,

        The authorization page lists allowed scopes
        If the client is configured to skip the authorization page, directly
        redirects to the requested URI
        """
        client = (
            http.request.env["oauth.provider.client"]
            .sudo()
            .search(
                [
                    ("identifier", "=", client_id),
                ]
            )
        )
        if not client:
            return http.request.render(
                "oauth_provider.authorization_error",
                {
                    "title": "Unknown Client Identifier!",
                    "message": "This client identifier is invalid.",
                },
            )
        oauth2_server = client.get_oauth2_server()

        # Retrieve needed arguments for oauthlib methods
        uri, http_method, body, headers = self._get_request_information()
        try:
            scopes, credentials = oauth2_server.validate_authorization_request(
                uri, http_method=http_method, body=body, headers=headers
            )
            # Store only some values, because the pickling of the full request
            # object is not possible
            http.request.session["oauth_scopes"] = scopes
            http.request.session["oauth_credentials"] = {
                "client_id": credentials["client_id"],
                "redirect_uri": credentials["redirect_uri"],
                "response_type": credentials["response_type"],
                "state": credentials["state"],
            }
            if client.skip_authorization:
                # Skip the authorization page
                # Useful when the application is trusted
                return self.authorize_post()
        except oauth2.FatalClientError as e:
            return http.request.render(
                "oauth_provider.authorization_error",
                {
                    "title": f"Error: {e.error}",
                    "message": e.description,
                },
            )
        except oauth2.OAuth2Error as e:
            return http.request.render(
                "oauth_provider.authorization_error",
                {
                    "title": f"Error: {e.error}",
                    "message": "An unknown error occured! Please contact your "
                    "administrator",
                },
            )

        oauth_scopes = client.scope_ids.filtered(lambda record: record.code in scopes)
        return http.request.render(
            "oauth_provider.authorization",
            {
                "oauth_client": client.name,
                "oauth_scopes": oauth_scopes,
            },
        )

    @http.route(
        "/oauth2/authorize", type="http", auth="user", methods=["POST"], website=True
    )
    def authorize_post(self, *args, **kwargs):
        """Redirect to the requested URI during the authorization"""
        client = (
            http.request.env["oauth.provider.client"]
            .sudo()
            .search(
                [
                    (
                        "identifier",
                        "=",
                        http.request.session.get("oauth_credentials", {}).get(
                            "client_id"
                        ),
                    )
                ]
            )
        )
        if not client:
            return http.request.render(
                "oauth_provider.authorization_error",
                {
                    "title": "Unknown Client Identifier!",
                    "message": "This client identifier is invalid.",
                },
            )
        oauth2_server = client.get_oauth2_server()

        # Retrieve needed arguments for oauthlib methods
        uri, http_method, body, headers = self._get_request_information()
        scopes = http.request.session["oauth_scopes"]
        credentials = http.request.session["oauth_credentials"]
        headers, body, status = oauth2_server.create_authorization_response(
            uri,
            http_method=http_method,
            body=body,
            headers=headers,
            scopes=scopes,
            credentials=credentials,
        )

        return werkzeug.utils.redirect(headers["Location"], code=status)

    @http.route(
        "/oauth2/token",
        type="http",
        auth="none",
        methods=["POST"],
        csrf=False,
        website=True,
    )
    def token(
        self,
        client_id=None,
        client_secret=None,
        redirect_uri=None,
        scope=None,
        code=None,
        grant_type=None,
        username=None,
        password=None,
        refresh_token=None,
        *args,
        **kwargs,
    ):
        """Return a token corresponding to the supplied information

        Not all parameters are required, depending on the application type
        """
        ensure_db()

        # If no client_id is specified, get it from session
        if client_id is None:
            client_id = http.request.session.get("oauth_credentials", {}).get(
                "client_id"
            )

        # Get from headers if available
        if client_id is None:
            auth_header = http.request.httprequest.headers.get("Authorization")
            basic = "basic "
            if auth_header and auth_header.lower().startswith(basic):
                client_id = (
                    base64.b64decode(auth_header[len(basic) :])
                    .decode("utf8")
                    .split(":")[0]
                )

        client = (
            http.request.env["oauth.provider.client"]
            .sudo()
            .search(
                [
                    ("identifier", "=", client_id),
                ]
            )
        )

        if not client:
            return self._json_response(data={"error": "invalid_client_id"}, status=401)
        oauth2_server = client.get_oauth2_server()

        # Retrieve needed arguments for oauthlib methods
        uri, http_method, body, headers = self._get_request_information()
        credentials = {"scope": " ".join(client.scope_ids.mapped("code"))}

        # Retrieve the authorization code, if any, to get Odoo's user id
        existing_code = (
            http.request.env["oauth.provider.authorization.code"]
            .sudo()
            .search(
                [
                    ("client_id.identifier", "=", client_id),
                    ("code", "=", code),
                ]
            )
        )
        if existing_code:
            credentials["odoo_user_id"] = existing_code.user_id.id
        # Retrieve the existing token, if any, to get Odoo's user id
        existing_token = (
            http.request.env["oauth.provider.token"]
            .sudo()
            .search(
                [
                    ("client_id.identifier", "=", client_id),
                    ("refresh_token", "=", refresh_token),
                ]
            )
        )
        if refresh_token and existing_token:
            credentials["odoo_user_id"] = existing_token.user_id.id

        headers, body, status = oauth2_server.create_token_response(
            uri,
            http_method=http_method,
            body=body,
            headers=headers,
            credentials=credentials,
        )

        return werkzeug.Response(body, status=status, headers=headers)

    @http.route(
        "/oauth2/tokeninfo", type="http", auth="none", methods=["GET"], website=True
    )
    def tokeninfo(self, access_token=None, *args, **kwargs):
        """Return some information about the supplied token

        Similar to Google's "tokeninfo" request
        """
        ensure_db()
        if not access_token:
            auth_header = http.request.httprequest.headers.get("Authorization", "")
            if auth_header.startswith("Bearer "):
                access_token = auth_header[7:]
        token = self._check_access_token(access_token)
        if not token:
            return self._json_response(
                data={"error": "invalid_or_expired_token"}, status=401
            )

        token_lifetime = (token.expires_at - datetime.now()).seconds
        # Base data to return
        data = {
            "audience": token.client_id.identifier,
            "scopes": " ".join(token.scope_ids.mapped("code")),
            "expires_in": token_lifetime,
        }

        # Add the oauth user identifier, if user's information access is
        # allowed by the token's scopes
        user_data = token._get_data_for_model("res.users", res_id=token.user_id.id)
        data.update(user_data)
        if "id" in user_data:
            data.update(user_id=token._generate_user_id())
        return self._json_response(data=data)

    @http.route(
        "/oauth2/userinfo", type="http", auth="none", methods=["GET"], website=True
    )
    def userinfo(self, access_token=None, *args, **kwargs):
        """Return some information about the user linked to the supplied token

        Similar to Google's "userinfo" request
        """
        ensure_db()
        if not access_token:
            auth_header = http.request.httprequest.headers.get("Authorization", "")
            if auth_header.startswith("Bearer "):
                access_token = auth_header[7:]
        token = self._check_access_token(access_token)
        if not token:
            return self._json_response(
                data={"error": "invalid_or_expired_token"}, status=401
            )

        data = token._get_data_for_model("res.users", res_id=token.user_id.id)
        return self._json_response(data=data)

    @http.route(
        "/oauth2/resources/<string:model>",
        type="http",
        auth="oauth_provider",
        methods=["GET"],
        website=True,
    )
    def protected_resource(
        self, model, access_token=None, resource_id=None, *args, **kwargs
    ):
        """Return allowed information about the requested model

        This endpoint follows OAuth 2.0 RFC 6749 for protected resource access.
        It requires a valid access token and appropriate scopes.
        """
        ensure_db()

        # Extract token from Authorization header if not provided as parameter
        if not access_token:
            auth_header = http.request.httprequest.headers.get("Authorization", "")
            if auth_header.startswith("Bearer "):
                access_token = auth_header[7:]  # Remove "Bearer " prefix
            else:
                return self._json_response(
                    data={
                        "error": "invalid_request",
                        "error_description": (
                            "Missing access token. Use Authorization: Bearer "
                            "<token> header or access_token parameter."
                        ),
                    },
                    status=401,
                )

        # Validate the access token
        token = self._check_access_token(access_token)
        if not token:
            return self._json_response(
                data={
                    "error": "invalid_token",
                    "error_description": (
                        "The access token provided is expired, revoked, "
                        "malformed, or invalid."
                    ),
                },
                status=401,
            )

        # Validate that the model exists and is accessible
        try:
            model_obj = (
                http.request.env["ir.model"]
                .sudo()
                .search([("model", "=", model)], limit=1)
            )
            if not model_obj:
                return self._json_response(
                    data={
                        "error": "invalid_resource",
                        "error_description": (
                            f"The requested resource model '{model}' does not exist."
                        ),
                    },
                    status=404,
                )

            # Check if the token has appropriate scopes for this model
            allowed_scopes = token.scope_ids.filtered(lambda s: s.model == model)
            if not allowed_scopes:
                return self._json_response(
                    data={
                        "error": "insufficient_scope",
                        "error_description": (
                            f"The access token does not have the required "
                            f"scope to access '{model}' resources."
                        ),
                    },
                    status=403,
                )

            # Get data based on scopes and optional resource_id filter
            res_id = None
            if resource_id:
                try:
                    res_id = int(resource_id)
                except (ValueError, TypeError):
                    return self._json_response(
                        data={
                            "error": "invalid_request",
                            "error_description": (
                                "Invalid resource_id format. Must be an integer."
                            ),
                        },
                        status=400,
                    )

            data = token._get_data_for_model(model, res_id=res_id)

            # Return structured response following OAuth 2.0 best practices
            response_data = {
                "resource": model,
                "data": data,
                "scope": " ".join(allowed_scopes.mapped("code")),
                "client_id": token.client_id.identifier,
            }

            if res_id:
                response_data["resource_id"] = res_id

            return self._json_response(data=response_data)

        except Exception as e:
            _logger.error("Error accessing protected resource: %s", str(e))
            return self._json_response(
                data={
                    "error": "server_error",
                    "error_description": (
                        "An internal server error occurred while "
                        "processing the request."
                    ),
                },
                status=500,
            )

    @http.route(
        "/oauth2/otherinfo",
        type="http",
        auth="none",
        methods=["GET"],
        website=True,
    )
    def otherinfo(self, access_token=None, model=None, *args, **kwargs):
        """Legacy endpoint for backward compatibility

        DEPRECATED: Use /oauth2/resources/<model> instead.
        This endpoint is maintained for backward compatibility but should
        not be used in new implementations.
        """
        _logger.warning(
            "DEPRECATED: /oauth2/otherinfo endpoint is deprecated. "
            "Use /oauth2/resources/<model> instead."
        )

        if not model:
            return self._json_response(
                data={
                    "error": "invalid_request",
                    "error_description": "Missing required 'model' parameter.",
                },
                status=400,
            )

        # Redirect to new endpoint implementation
        return self.protected_resource(model, access_token, *args, **kwargs)

    @http.route(
        "/oauth2/revoke_token", type="http", auth="none", methods=["POST"], website=True
    )
    def revoke_token(self, token=None, *args, **kwargs):
        """Revoke the supplied token"""
        ensure_db()
        body = oauthlib.common.urlencode(http.request.httprequest.values.items())
        db_token = (
            http.request.env["oauth.provider.token"]
            .sudo()
            .search(
                [
                    ("token", "=", token),
                ]
            )
        )
        if not db_token:
            db_token = (
                http.request.env["oauth.provider.token"]
                .sudo()
                .search(
                    [
                        ("refresh_token", "=", token),
                    ]
                )
            )
        if not db_token:
            return self._json_response(
                data={"error": "invalid_or_expired_token"}, status=401
            )
        oauth2_server = db_token.client_id.get_oauth2_server()

        # Retrieve needed arguments for oauthlib methods
        uri, http_method, body, headers = self._get_request_information()

        headers, body, status = oauth2_server.create_revocation_response(
            uri, http_method=http_method, body=body, headers=headers
        )
        return werkzeug.Response(body, status=status, headers=headers)
