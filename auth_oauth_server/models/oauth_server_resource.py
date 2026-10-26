# Copyright 2026 Lorenzo Battistini
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import re

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

from ..exceptions import InsufficientScope, OAuthError
from ..utils import generate_token, normalize_uri

WELL_KNOWN_RESOURCE = "/.well-known/oauth-protected-resource"


class OAuthServerResource(models.Model):
    """An API of this Odoo that accepts the access tokens of the server.

    Each resource has its own JWT validator, which signs and checks its
    tokens: a token issued for one resource is refused by every other.
    """

    _name = "oauth.server.resource"
    _description = "OAuth Protected Resource"
    _order = "name, id"

    name = fields.Char(required=True)
    path = fields.Char(
        required=True,
        help="Path of the API on this server, such as /api. Its URI, which "
        "applications ask tokens for, is the issuer URL followed by this path.",
    )
    uri = fields.Char(string="URI", compute="_compute_uri")
    scopes = fields.Char(
        help="Space-separated scopes applications may ask for. Tokens get "
        "all of them unless the application asks for fewer."
    )
    group_ids = fields.Many2many(
        "res.groups",
        string="Allowed Groups",
        help="Users in one of these groups may connect applications to this "
        "resource. Leave empty to allow every internal user.",
    )
    access_token_lifetime = fields.Integer(
        string="Access Token Lifetime (seconds)", default=600, required=True
    )
    refresh_token_lifetime = fields.Integer(
        string="Refresh Token Lifetime (days)",
        default=30,
        required=True,
        help="An application that does not connect for this long must be "
        "authorized again.",
    )
    max_lifetime = fields.Integer(
        string="Authorization Lifetime (days)",
        default=90,
        required=True,
        help="After this many days the user must authorize the application "
        "again, however often it connects.",
    )
    jwt_validator_id = fields.Many2one(
        "auth.jwt.validator",
        string="JWT Validator",
        required=True,
        readonly=True,
        copy=False,
        ondelete="cascade",
    )
    authorization_ids = fields.One2many(
        "oauth.server.authorization", "resource_id", readonly=True
    )
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ("path_uniq", "unique(path)", "Another resource already uses this path."),
        (
            "lifetimes_positive",
            "CHECK(access_token_lifetime > 0 AND refresh_token_lifetime > 0 "
            "AND max_lifetime > 0)",
            "Lifetimes must be positive.",
        ),
    ]

    @api.constrains("path")
    def _check_path(self):
        for resource in self:
            path = resource.path
            if (
                not path.startswith("/")
                or (path != "/" and path.endswith("/"))
                or re.search(r"[\s?#]", path)
            ):
                raise ValidationError(
                    _(
                        "The path %(path)s must start with a slash, and contain "
                        "no trailing slash, query or fragment.",
                        path=path,
                    )
                )

    @api.model
    def _uri_for_path(self, path):
        issuer = self.env["oauth.server"]._get_issuer()
        return issuer if path == "/" else issuer + (path or "")

    @api.depends("path")
    def _compute_uri(self):
        for resource in self:
            resource.uri = self._uri_for_path(resource.path)

    @api.model
    def _create_jwt_validator(self, path):
        validators = self.env["auth.jwt.validator"].sudo()
        base = "oauth_server_" + (re.sub(r"\W+", "_", path or "").strip("_") or "root")
        name, counter = base, 1
        while validators.search_count([("name", "=", name)]):
            counter += 1
            name = "%s_%s" % (base, counter)
        return validators.create(
            {
                "name": name,
                "signature_type": "secret",
                "secret_key": generate_token(48),
                "secret_algorithm": "HS256",
                "audience": self._uri_for_path(path),
                "issuer": self.env["oauth.server"]._get_issuer(),
                "user_id_strategy": "oauth_server",
                "static_user_id": False,
                "cookie_enabled": False,
            }
        )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("jwt_validator_id"):
                validator = self._create_jwt_validator(vals.get("path"))
                vals["jwt_validator_id"] = validator.id
        return super().create(vals_list)

    def write(self, vals):
        res = super().write(vals)
        if "path" in vals:
            self._sync_jwt_validator()
        return res

    def unlink(self):
        validators = self.jwt_validator_id
        res = super().unlink()
        validators.sudo().unlink()
        return res

    def _sync_jwt_validator(self):
        """Follow a change of issuer or path in the validator's iss and aud."""
        self.invalidate_recordset(["uri"])
        issuer = self.env["oauth.server"]._get_issuer()
        for resource in self:
            validator = resource.jwt_validator_id.sudo()
            if validator.issuer != issuer or validator.audience != resource.uri:
                validator.write({"issuer": issuer, "audience": resource.uri})

    def action_rotate_secret(self):
        """Invalidate every access token of the resource at once.

        Applications get a new access token with their refresh token.
        """
        for resource in self:
            resource.jwt_validator_id.sudo().secret_key = generate_token(48)

    # ------------------------------------------------------------------
    # Requests
    # ------------------------------------------------------------------

    def _get_scopes(self):
        self.ensure_one()
        return (self.scopes or "").split()

    def _filter_scopes(self, requested):
        """The scopes to grant for a request: unknown ones are dropped (RFC
        6749 3.3), and no request at all means every scope."""
        allowed = self._get_scopes()
        if isinstance(requested, str):
            kept = [scope for scope in requested.split() if scope in allowed]
            if kept:
                return " ".join(dict.fromkeys(kept))
        return " ".join(allowed)

    @api.model
    def _get_by_uri(self, uri):
        normalized = normalize_uri(uri)
        if not normalized:
            return self.browse()
        for resource in self.search([]):
            if normalize_uri(resource.uri) == normalized:
                return resource
        return self.browse()

    @api.model
    def _get_for_request(self, uri):
        """The resource named by an RFC 8707 resource parameter.

        Without one, the only active resource is used, if there is only one.
        """
        if uri:
            resource = self._get_by_uri(uri)
            if not resource:
                raise OAuthError("invalid_target", "Unknown resource.")
            return resource
        resources = self.search([])
        if len(resources) != 1:
            raise OAuthError("invalid_target", "The resource parameter is required.")
        return resources

    def _is_user_allowed(self, user):
        self.ensure_one()
        user = user.sudo()
        if not user.active:
            return False
        if self.group_ids:
            return bool(self.group_ids & user.groups_id)
        return user._is_internal()

    # ------------------------------------------------------------------
    # Helpers for the controllers of the resource
    # ------------------------------------------------------------------

    def _get_metadata_url(self):
        self.ensure_one()
        issuer = self.env["oauth.server"]._get_issuer()
        path = "" if self.path == "/" else self.path
        return issuer + WELL_KNOWN_RESOURCE + path

    def _metadata(self):
        """Protected resource metadata (RFC 9728)."""
        self.ensure_one()
        return {
            "resource": self.uri,
            "authorization_servers": [self.env["oauth.server"]._get_issuer()],
            "scopes_supported": self._get_scopes(),
            "bearer_methods_supported": ["header"],
            "resource_name": self.name,
        }

    def _www_authenticate(self, error=None, error_description=None, scope=None):
        """Value of the WWW-Authenticate header of a 401 or 403 answer.

        It points clients to the resource metadata, from which they discover
        the authorization server (RFC 9728 5.1).
        """
        self.ensure_one()
        scope = self.scopes if scope is None else scope
        params = [("resource_metadata", self._get_metadata_url())]
        if scope:
            params.append(("scope", scope))
        if error:
            params.append(("error", error))
        if error_description:
            params.append(("error_description", error_description))
        return "Bearer " + ", ".join(
            '%s="%s"' % (key, value.replace("\\", "\\\\").replace('"', '\\"'))
            for key, value in params
        )

    def _authenticate_bearer(self, token, required_scopes=None):
        """Check an access token presented to this resource.

        Returns ``(uid, payload)``. Raises werkzeug's Unauthorized for an
        invalid, expired or revoked token, and InsufficientScope when the
        token lacks one of ``required_scopes``.
        """
        self.ensure_one()
        validator = self.jwt_validator_id.sudo()
        payload = validator._decode(token)
        uid = validator._get_and_check_uid(payload)
        required = list(required_scopes or [])
        granted = set((payload.get("scope") or "").split())
        if not set(required) <= granted:
            raise InsufficientScope(" ".join(required))
        return uid, payload
