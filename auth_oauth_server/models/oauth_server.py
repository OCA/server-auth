# Copyright 2026 Lorenzo Battistini
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from urllib.parse import unquote_plus

from odoo import api, models
from odoo.tools import str2bool

from ..exceptions import OAuthError
from ..utils import (
    PKCE_CHALLENGE_RE,
    is_valid_redirect_uri,
    redirect_uri_matches,
    sign,
    verify,
)

AUTH_METHODS = ("none", "client_secret_basic", "client_secret_post")
CONSENT_SCOPE = "auth_oauth_server.consent"
# time the user has to answer the consent page
CONSENT_MAX_AGE = 600
MAX_STATE_LENGTH = 2048


class OAuthServer(models.AbstractModel):
    """The authorization server: configuration, metadata and the steps of the
    authorization code flow that are not tied to one record."""

    _name = "oauth.server"
    _description = "OAuth Authorization Server"

    # ------------------------------------------------------------------
    # Configuration
    # ------------------------------------------------------------------

    @api.model
    def _get_issuer(self):
        params = self.env["ir.config_parameter"].sudo()
        issuer = params.get_param("auth_oauth_server.issuer") or params.get_param(
            "web.base.url"
        )
        return (issuer or "").rstrip("/")

    @api.model
    def _get_bool_param(self, key):
        value = self.env["ir.config_parameter"].sudo().get_param(key)
        return str2bool(value or "False", False)

    @api.model
    def _is_metadata_document_enabled(self):
        return self._get_bool_param("auth_oauth_server.cimd_enabled")

    @api.model
    def _is_dynamic_registration_enabled(self):
        return self._get_bool_param("auth_oauth_server.dcr_enabled")

    @api.model
    def _get_trusted_metadata_domains(self):
        value = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("auth_oauth_server.cimd_trusted_domains")
        )
        return [
            domain.strip().lower().lstrip(".")
            for domain in (value or "").split(",")
            if domain.strip()
        ]

    @api.model
    def _metadata(self):
        """Authorization server metadata (RFC 8414)."""
        issuer = self._get_issuer()
        resources = self.env["oauth.server.resource"].search([])
        scopes = sorted({scope for res in resources for scope in res._get_scopes()})
        metadata = {
            "issuer": issuer,
            "authorization_endpoint": issuer + "/oauth/authorize",
            "token_endpoint": issuer + "/oauth/token",
            "revocation_endpoint": issuer + "/oauth/revoke",
            "response_types_supported": ["code"],
            "response_modes_supported": ["query"],
            "grant_types_supported": ["authorization_code", "refresh_token"],
            "code_challenge_methods_supported": ["S256"],
            "token_endpoint_auth_methods_supported": list(AUTH_METHODS),
            "revocation_endpoint_auth_methods_supported": list(AUTH_METHODS),
            "scopes_supported": scopes,
            "authorization_response_iss_parameter_supported": True,
            "client_id_metadata_document_supported": (
                self._is_metadata_document_enabled()
            ),
        }
        if self._is_dynamic_registration_enabled():
            metadata["registration_endpoint"] = issuer + "/oauth/register"
        return metadata

    # ------------------------------------------------------------------
    # Authorization request
    # ------------------------------------------------------------------

    @api.model
    def _get_authorization_client(self, params):
        """The client and redirect URI of an authorization request.

        The errors raised here must be shown to the user, never redirected:
        the redirect URI is not trusted yet.
        """
        identifier = params.get("client_id")
        if not identifier or not isinstance(identifier, str):
            raise OAuthError("invalid_request", "Missing client_id.")
        client = self.env["oauth.server.client"]._get_for_authorization(identifier)
        registered = client._get_redirect_uris()
        redirect_uri = params.get("redirect_uri")
        if not redirect_uri:
            if len(registered) != 1:
                raise OAuthError("invalid_request", "Missing redirect_uri.")
            redirect_uri = registered[0]
        if not is_valid_redirect_uri(redirect_uri) or not any(
            redirect_uri_matches(uri, redirect_uri) for uri in registered
        ):
            raise OAuthError("invalid_request", "Unregistered redirect_uri.")
        return client, redirect_uri

    @api.model
    def _check_authorization_request(self, client, redirect_uri, params, user):
        """Validate an authorization request for ``user``.

        Returns the values to sign into the consent page, from which the
        decision is taken once the user answers.
        """
        if params.get("response_type") != "code":
            raise OAuthError(
                "unsupported_response_type", "Only the code response type is supported."
            )
        challenge = params.get("code_challenge")
        if (
            params.get("code_challenge_method") != "S256"
            or not isinstance(challenge, str)
            or not PKCE_CHALLENGE_RE.match(challenge)
        ):
            raise OAuthError(
                "invalid_request", "PKCE with the S256 method is required."
            )
        state = params.get("state")
        if state is not None and len(state) > MAX_STATE_LENGTH:
            raise OAuthError("invalid_request", "The state parameter is too long.")
        resource = self.env["oauth.server.resource"]._get_for_request(
            params.get("resource")
        )
        if not resource._is_user_allowed(user):
            raise OAuthError(
                "access_denied", "This user may not give access to this resource."
            )
        return {
            "client": client.id,
            "redirect_uri": redirect_uri,
            "resource": resource.id,
            "scope": resource._filter_scopes(params.get("scope")),
            "code_challenge": challenge,
            "state": state,
            "uid": user.id,
        }

    @api.model
    def _get_consent_secret(self):
        return self.env["ir.config_parameter"].sudo().get_param("database.secret")

    @api.model
    def _sign_consent(self, values):
        return sign(self._get_consent_secret(), CONSENT_SCOPE, values, CONSENT_MAX_AGE)

    @api.model
    def _verify_consent(self, signed):
        return verify(self._get_consent_secret(), CONSENT_SCOPE, signed)

    @api.model
    def _approve(self, values, user):
        """Record the user's consent; returns the authorization code."""
        client = self.env["oauth.server.client"].browse(values["client"]).exists()
        resource = self.env["oauth.server.resource"].browse(values["resource"]).exists()
        if not client.active or not resource.active:
            raise OAuthError("invalid_request", "The application is no longer allowed.")
        if not resource._is_user_allowed(user):
            raise OAuthError(
                "access_denied", "This user may not give access to this resource."
            )
        _authorization, code = self.env[
            "oauth.server.authorization"
        ]._create_from_consent(
            user,
            client,
            resource,
            values["scope"],
            values["redirect_uri"],
            values["code_challenge"],
        )
        return code

    # ------------------------------------------------------------------
    # Client authentication (token and revocation endpoints)
    # ------------------------------------------------------------------

    @api.model
    def _authenticate_client(self, client_id, client_secret, basic=None):
        """The client of a token or revocation request.

        ``basic`` is the (username, password) pair of an HTTP Basic
        Authorization header, if any. Confidential clients must present
        their secret; public clients are identified by client_id alone.
        """
        if basic:
            basic_id, basic_secret = (unquote_plus(value or "") for value in basic)
            if client_id and client_id != basic_id:
                raise OAuthError("invalid_request", "Conflicting client_id.")
            client_id, client_secret = basic_id, basic_secret
        failure = OAuthError("invalid_client", "Client authentication failed.", 401)
        if not client_id or not isinstance(client_id, str):
            raise failure
        client = self.env["oauth.server.client"].search(
            [("identifier", "=", client_id)], limit=1
        )
        if not client:
            raise failure
        if client.client_type == "confidential" and not client._check_secret(
            client_secret
        ):
            raise failure
        return client
