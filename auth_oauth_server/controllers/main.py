# Copyright 2026 Lorenzo Battistini
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import json
import logging
from urllib.parse import urlsplit

from odoo import SUPERUSER_ID, http
from odoo.http import request

from ..exceptions import OAuthError
from ..utils import add_query, is_loopback_host

_logger = logging.getLogger(__name__)

NO_STORE = [("Cache-Control", "no-store"), ("Pragma", "no-cache")]
PAGE_HEADERS = NO_STORE + [
    ("X-Frame-Options", "DENY"),
    ("Content-Security-Policy", "frame-ancestors 'none'"),
    ("Referrer-Policy", "no-referrer"),
]
MAX_REGISTRATION_BODY = 16 * 1024


class OAuthServerController(http.Controller):
    """Endpoints of the authorization server.

    They only parse requests and serialize answers: the flow is implemented
    by the models. OAuthError raised by the models is turned into a response
    here rather than propagated, so what a model did before failing, such as
    revoking an authorization whose code was reused, is committed.
    """

    @staticmethod
    def _env():
        # unauthenticated endpoints: auth="none" leaves no user in request.env
        return request.env(user=SUPERUSER_ID, su=True)

    @staticmethod
    def _json_response(data, status=200, headers=None):
        return request.make_json_response(
            data, headers=(headers or []) + NO_STORE, status=status
        )

    def _oauth_error_response(self, error):
        headers = []
        if error.status == 401:
            headers.append(("WWW-Authenticate", 'Basic realm="oauth"'))
        return self._json_response(
            error.to_dict(), status=error.status, headers=headers
        )

    # ------------------------------------------------------------------
    # Metadata
    # ------------------------------------------------------------------

    @http.route(
        "/.well-known/oauth-authorization-server",
        type="http",
        auth="none",
        methods=["GET"],
        cors="*",
        csrf=False,
        save_session=False,
    )
    def authorization_server_metadata(self):
        return self._json_response(self._env()["oauth.server"]._metadata())

    @http.route(
        [
            "/.well-known/oauth-protected-resource",
            "/.well-known/oauth-protected-resource/<path:path>",
        ],
        type="http",
        auth="none",
        methods=["GET"],
        cors="*",
        csrf=False,
        save_session=False,
    )
    def protected_resource_metadata(self, path=""):
        resource = self._env()["oauth.server.resource"].search(
            [("path", "=", "/" + path)], limit=1
        )
        if not resource:
            return self._json_response({"error": "not_found"}, status=404)
        return self._json_response(resource._metadata())

    # ------------------------------------------------------------------
    # Authorization endpoint
    # ------------------------------------------------------------------

    @http.route(
        "/oauth/authorize",
        type="http",
        auth="public",
        methods=["GET"],
        website=True,
        multilang=False,
        sitemap=False,
    )
    def authorize(self, **params):
        if request.env.user._is_public():
            # nothing is checked, and no metadata document fetched, for
            # anonymous visitors: the login page brings them back here
            return request.redirect_query(
                "/web/login", {"redirect": request.httprequest.full_path}
            )
        server = self._env()["oauth.server"]
        try:
            client, redirect_uri = server._get_authorization_client(params)
        except OAuthError as error:
            return self._error_page(error)
        try:
            values = server._check_authorization_request(
                client, redirect_uri, params, request.env.user
            )
        except OAuthError as error:
            if client.registration_type != "manual":
                # the redirect URI of a self-registered client may belong to
                # anyone: never send the user there without their consent
                return self._error_page(error)
            return self._redirect_to_client(
                redirect_uri,
                {
                    "error": error.error,
                    "error_description": error.description,
                    "state": params.get("state"),
                },
            )
        return self._consent_page(client, values)

    @http.route(
        "/oauth/authorize/decision",
        type="http",
        auth="public",
        methods=["POST"],
        website=True,
        multilang=False,
        sitemap=False,
    )
    def authorize_decision(self, consent=None, decision=None, **kwargs):
        user = request.env.user
        server = self._env()["oauth.server"]
        values = None if user._is_public() else server._verify_consent(consent)
        if not values or values.get("uid") != user.id:
            return self._error_page(
                OAuthError(
                    "invalid_request",
                    "The authorization request expired: start again from the "
                    "application.",
                )
            )
        if decision != "approve":
            return self._redirect_to_client(
                values["redirect_uri"],
                {
                    "error": "access_denied",
                    "error_description": "The user denied the request.",
                    "state": values.get("state"),
                },
            )
        try:
            code = server._approve(values, user)
        except OAuthError as error:
            return self._error_page(error)
        return self._redirect_to_client(
            values["redirect_uri"], {"code": code, "state": values.get("state")}
        )

    def _redirect_to_client(self, redirect_uri, params):
        params = dict(params, iss=self._env()["oauth.server"]._get_issuer())
        return request.redirect(add_query(redirect_uri, params), local=False)

    def _consent_page(self, client, values):
        env = self._env()
        redirect_host = urlsplit(values["redirect_uri"]).hostname
        is_document = client.registration_type == "metadata_document"
        qcontext = {
            "client": client,
            "client_host": urlsplit(client.identifier).hostname if is_document else "",
            "unverified": client.registration_type == "dynamic",
            "redirect_host": redirect_host,
            "loopback": is_loopback_host(redirect_host),
            "resource": env["oauth.server.resource"].browse(values["resource"]),
            "scopes": values["scope"].split(),
            "user": request.env.user,
            "consent": env["oauth.server"]._sign_consent(values),
        }
        return self._page("auth_oauth_server.consent_page", qcontext)

    def _error_page(self, error):
        return self._page("auth_oauth_server.error_page", {"error": error}, 400)

    @staticmethod
    def _page(template, qcontext, status=200):
        response = request.render(template, qcontext, status=status)
        for key, value in PAGE_HEADERS:
            response.headers[key] = value
        return response

    # ------------------------------------------------------------------
    # Token, revocation and registration endpoints
    # ------------------------------------------------------------------

    @staticmethod
    def _basic_credentials():
        authorization = request.httprequest.authorization
        if authorization and authorization.type == "basic":
            return authorization.username, authorization.password
        return None

    @http.route(
        "/oauth/token",
        type="http",
        auth="none",
        methods=["POST"],
        cors="*",
        csrf=False,
        save_session=False,
    )
    def token(self, **params):
        env = self._env()
        try:
            client = env["oauth.server"]._authenticate_client(
                params.get("client_id"),
                params.get("client_secret"),
                self._basic_credentials(),
            )
            grant_type = params.get("grant_type")
            authorizations = env["oauth.server.authorization"]
            if grant_type == "authorization_code":
                result = authorizations._exchange_code(client, params)
            elif grant_type == "refresh_token":
                result = authorizations._refresh(client, params)
            else:
                raise OAuthError("unsupported_grant_type", "Unsupported grant_type.")
        except OAuthError as error:
            return self._oauth_error_response(error)
        return self._json_response(result)

    @http.route(
        "/oauth/revoke",
        type="http",
        auth="none",
        methods=["POST"],
        cors="*",
        csrf=False,
        save_session=False,
    )
    def revoke(self, **params):
        env = self._env()
        try:
            client = env["oauth.server"]._authenticate_client(
                params.get("client_id"),
                params.get("client_secret"),
                self._basic_credentials(),
            )
        except OAuthError as error:
            return self._oauth_error_response(error)
        env["oauth.server.authorization"]._revoke_token(client, params.get("token"))
        return request.make_response("", headers=NO_STORE)

    @http.route(
        "/oauth/register",
        type="http",
        auth="none",
        methods=["POST"],
        cors="*",
        csrf=False,
        save_session=False,
    )
    def register(self):
        env = self._env()
        if not env["oauth.server"]._is_dynamic_registration_enabled():
            return self._json_response({"error": "not_found"}, status=404)
        length = request.httprequest.content_length
        try:
            if not length or length > MAX_REGISTRATION_BODY:
                raise OAuthError(
                    "invalid_client_metadata",
                    "The registration request is missing or too large.",
                )
            try:
                metadata = json.loads(request.httprequest.get_data(as_text=True))
            except ValueError as exc:
                raise OAuthError(
                    "invalid_client_metadata", "The request is not valid JSON."
                ) from exc
            result = env["oauth.server.client"]._register_dynamic(metadata)
        except OAuthError as error:
            return self._oauth_error_response(error)
        return self._json_response(result, status=201)
