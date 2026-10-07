# Copyright 2026 Lorenzo Battistini
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import logging
import time
from datetime import timedelta
from urllib.parse import urlsplit

import requests

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools import consteq

from .. import utils
from ..exceptions import OAuthError
from .oauth_server import AUTH_METHODS

_logger = logging.getLogger(__name__)

MAX_REDIRECT_URIS = 10
MAX_NAME_LENGTH = 200


class OAuthServerClient(models.Model):
    """An application that may ask users for access tokens."""

    _name = "oauth.server.client"
    _description = "OAuth Client"
    _order = "name, id"

    name = fields.Char(required=True)
    identifier = fields.Char(
        string="Client ID",
        required=True,
        readonly=True,
        copy=False,
        default=lambda self: utils.generate_token(18),
    )
    registration_type = fields.Selection(
        [
            ("manual", "Manual"),
            ("dynamic", "Dynamic Registration"),
            ("metadata_document", "Metadata Document"),
        ],
        default="manual",
        required=True,
        readonly=True,
        help="Manual: created here. Dynamic Registration: the application "
        "registered itself, so its name is not verified. Metadata Document: "
        "the Client ID is the URL where the application publishes its details.",
    )
    client_type = fields.Selection(
        [("public", "Public"), ("confidential", "Confidential")],
        default="public",
        required=True,
        help="Confidential clients authenticate with a secret; public ones, "
        "such as desktop applications, rely on PKCE alone.",
    )
    client_secret_hash = fields.Char(readonly=True, copy=False)
    redirect_uris = fields.Text(
        string="Redirect URIs",
        required=True,
        help="One per line. https, or http on localhost; the port of localhost "
        "addresses may vary.",
    )
    client_uri = fields.Char(string="Homepage", readonly=True)
    metadata_expires_at = fields.Datetime(readonly=True)
    authorization_ids = fields.One2many(
        "oauth.server.authorization", "client_id", readonly=True
    )
    authorization_count = fields.Integer(compute="_compute_authorization_count")
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ("identifier_uniq", "unique(identifier)", "The Client ID must be unique."),
    ]

    @api.depends("authorization_ids")
    def _compute_authorization_count(self):
        for client in self:
            client.authorization_count = len(client.authorization_ids)

    @api.constrains("redirect_uris")
    def _check_redirect_uris(self):
        for client in self:
            uris = client._get_redirect_uris()
            if not uris:
                raise ValidationError(_("At least one redirect URI is required."))
            for uri in uris:
                if not utils.is_valid_redirect_uri(uri):
                    raise ValidationError(
                        _(
                            "Invalid redirect URI %(uri)s: use https, or http "
                            "on localhost, without fragment.",
                            uri=uri,
                        )
                    )

    def _get_redirect_uris(self):
        self.ensure_one()
        return [
            uri.strip()
            for uri in (self.redirect_uris or "").splitlines()
            if uri.strip()
        ]

    def _check_secret(self, secret):
        self.ensure_one()
        if not self.client_secret_hash or not isinstance(secret, str) or not secret:
            return False
        return consteq(utils.hash_token(secret), self.client_secret_hash)

    def action_generate_secret(self):
        """Make the client confidential with a new secret, shown only once."""
        self.ensure_one()
        secret = utils.generate_token()
        self.write(
            {
                "client_type": "confidential",
                "client_secret_hash": utils.hash_token(secret),
            }
        )
        return {
            "type": "ir.actions.act_window",
            "res_model": "oauth.server.client.secret",
            "name": _("Client Secret"),
            "views": [(False, "form")],
            "target": "new",
            "context": {
                "default_identifier": self.identifier,
                "default_secret": secret,
            },
        }

    # ------------------------------------------------------------------
    # Authorization requests
    # ------------------------------------------------------------------

    @api.model
    def _get_for_authorization(self, identifier):
        """The client named by the client_id of an authorization request.

        A client_id that is an https URL is resolved as a Client ID Metadata
        Document when that is enabled. This is the only place where the
        server fetches one: token and revocation requests use the stored
        client only.
        """
        client = self.with_context(active_test=False).search(
            [("identifier", "=", identifier)], limit=1
        )
        if client and not client.active:
            raise OAuthError("unauthorized_client", "This application is disabled.")
        is_document = (
            client.registration_type == "metadata_document"
            if client
            else utils.check_metadata_document_url(identifier)
        )
        if not is_document:
            if not client:
                raise OAuthError("invalid_client", "Unknown client.")
            return client
        if not self.env["oauth.server"]._is_metadata_document_enabled():
            raise OAuthError("invalid_client", "Unknown client.")
        return self._get_metadata_document_client(identifier, client)

    @api.model
    def _is_trusted_metadata_host(self, hostname):
        domains = self.env["oauth.server"]._get_trusted_metadata_domains()
        hostname = (hostname or "").lower()
        return not domains or any(
            hostname == domain or hostname.endswith("." + domain) for domain in domains
        )

    @api.model
    def _get_metadata_document_client(self, url, client):
        """Fetch (or reuse while fresh) the metadata document at ``url``."""
        now = fields.Datetime.now()
        if client and client.metadata_expires_at and client.metadata_expires_at > now:
            return client
        hostname = urlsplit(url).hostname
        if not self._is_trusted_metadata_host(hostname):
            raise OAuthError(
                "invalid_client", "Applications from this domain are not accepted."
            )
        try:
            addresses = utils.resolve_host(hostname)
        except OSError:
            addresses = set()
        if not addresses or not all(utils.is_public_address(a) for a in addresses):
            raise OAuthError(
                "invalid_client", "The client metadata host is not a public address."
            )
        try:
            document, cache_control = utils.fetch_metadata_document(url)
        except (requests.RequestException, ValueError) as error:
            _logger.info("Cannot fetch client metadata document %s: %s", url, error)
            raise OAuthError(
                "invalid_client", "Cannot fetch the client metadata document."
            ) from error
        values = self._get_metadata_document_values(url, document)
        values["metadata_expires_at"] = now + timedelta(
            seconds=utils.max_age_from_cache_control(cache_control)
        )
        if client:
            client.write(values)
            return client
        values.update(identifier=url, registration_type="metadata_document")
        return self.create(values)

    @api.model
    def _get_metadata_document_values(self, url, document):
        if not isinstance(document, dict) or document.get("client_id") != url:
            raise OAuthError(
                "invalid_client", "The client metadata document does not match its URL."
            )
        name = document.get("client_name")
        uris = document.get("redirect_uris")
        if not isinstance(name, str) or not name.strip() or len(name) > MAX_NAME_LENGTH:
            raise OAuthError("invalid_client", "Invalid client_name.")
        if not self._are_valid_redirect_uris(uris):
            raise OAuthError("invalid_client", "Invalid redirect_uris.")
        if document.get("token_endpoint_auth_method", "none") != "none":
            raise OAuthError(
                "invalid_client",
                "Only public clients may use a client metadata document.",
            )
        return {
            "name": name.strip(),
            "redirect_uris": "\n".join(uris),
            "client_uri": self._get_valid_client_uri(document.get("client_uri")),
            "client_type": "public",
        }

    @api.model
    def _are_valid_redirect_uris(self, uris):
        return (
            isinstance(uris, list)
            and 0 < len(uris) <= MAX_REDIRECT_URIS
            and all(utils.is_valid_redirect_uri(uri) for uri in uris)
        )

    @api.model
    def _get_valid_client_uri(self, uri):
        if (
            isinstance(uri, str)
            and uri.startswith("https://")
            and len(uri) <= utils.MAX_URI_LENGTH
        ):
            return uri
        return False

    # ------------------------------------------------------------------
    # Dynamic client registration (RFC 7591)
    # ------------------------------------------------------------------

    @api.model
    def _register_dynamic(self, metadata):
        """Register a client from an RFC 7591 request; returns the response.

        Fields the server does not use are ignored rather than rejected.
        """
        if not isinstance(metadata, dict):
            raise OAuthError(
                "invalid_client_metadata", "The request must be a JSON object."
            )
        uris = metadata.get("redirect_uris")
        if not self._are_valid_redirect_uris(uris):
            raise OAuthError(
                "invalid_redirect_uri",
                "Give 1 to %s redirect URIs using https, or http on localhost."
                % MAX_REDIRECT_URIS,
            )
        method = metadata.get("token_endpoint_auth_method", "client_secret_basic")
        if method not in AUTH_METHODS:
            raise OAuthError(
                "invalid_client_metadata", "Unsupported token_endpoint_auth_method."
            )
        grant_types = metadata.get("grant_types", ["authorization_code"])
        if (
            not isinstance(grant_types, list)
            or "authorization_code" not in grant_types
            or not set(grant_types) <= {"authorization_code", "refresh_token"}
        ):
            raise OAuthError("invalid_client_metadata", "Unsupported grant_types.")
        if metadata.get("response_types", ["code"]) != ["code"]:
            raise OAuthError("invalid_client_metadata", "Unsupported response_types.")
        name = metadata.get("client_name") or urlsplit(uris[0]).hostname
        if not isinstance(name, str) or len(name) > MAX_NAME_LENGTH:
            raise OAuthError("invalid_client_metadata", "Invalid client_name.")
        secret = utils.generate_token() if method != "none" else None
        client = self.create(
            {
                "name": name,
                "registration_type": "dynamic",
                "client_type": "confidential" if secret else "public",
                "client_secret_hash": secret and utils.hash_token(secret),
                "redirect_uris": "\n".join(uris),
                "client_uri": self._get_valid_client_uri(metadata.get("client_uri")),
            }
        )
        response = {
            "client_id": client.identifier,
            "client_id_issued_at": int(time.time()),
            "client_name": client.name,
            "redirect_uris": uris,
            "grant_types": grant_types,
            "response_types": ["code"],
            "token_endpoint_auth_method": method,
        }
        if client.client_uri:
            response["client_uri"] = client.client_uri
        if secret:
            response.update(client_secret=secret, client_secret_expires_at=0)
        return response

    @api.autovacuum
    def _gc_unused_clients(self):
        """Forget self-registered clients no user authorized within a day."""
        limit = fields.Datetime.now() - timedelta(days=1)
        self.with_context(active_test=False).search(
            [
                ("registration_type", "in", ("dynamic", "metadata_document")),
                ("create_date", "<", limit),
                ("authorization_ids", "=", False),
            ]
        ).unlink()


class OAuthServerClientSecret(models.AbstractModel):
    """Shows a new client secret once, without storing it (like API keys)."""

    _name = "oauth.server.client.secret"
    _description = "OAuth Client Secret"

    # the field 'id' is needed by the onchange that fills in the defaults
    id = fields.Id()
    identifier = fields.Char(string="Client ID", readonly=True)
    secret = fields.Char(readonly=True)
