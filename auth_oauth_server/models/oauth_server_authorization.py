# Copyright 2026 Lorenzo Battistini
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import calendar
import time
import uuid
from datetime import timedelta

import jwt  # pylint: disable=missing-manifest-dependency

from odoo import _, api, fields, models
from odoo.exceptions import AccessError

from odoo.addons.auth_jwt.exceptions import UnauthorizedInvalidToken

from ..exceptions import OAuthError
from ..utils import check_pkce, generate_token, hash_token, normalize_uri

# lifetime of an authorization code, in seconds
CODE_LIFETIME = 60
# a refresh token presented again this soon after its first use (in seconds)
# comes from concurrent requests of the same client, not from a stolen copy
REFRESH_REUSE_GRACE = 60


def _timestamp(value):
    """Unix timestamp of a naive UTC datetime, as Odoo stores them."""
    return calendar.timegm(value.utctimetuple())


class OAuthServerAuthorization(models.Model):
    """The consent a user gave an application for a resource.

    One record per approval: two installations of the same application, or
    two approvals on the same computer, are independent, so revoking (or
    detecting the theft of) one leaves the others working.
    """

    _name = "oauth.server.authorization"
    _description = "OAuth Authorization"
    _order = "create_date desc, id desc"
    _rec_name = "client_id"
    # users see their authorizations in their preferences: never let them
    # alter them through the sudo-ed write of res.users
    _allow_sudo_commands = False

    user_id = fields.Many2one(
        "res.users", required=True, readonly=True, ondelete="cascade", index=True
    )
    client_id = fields.Many2one(
        "oauth.server.client",
        string="Application",
        required=True,
        readonly=True,
        ondelete="cascade",
        index=True,
    )
    resource_id = fields.Many2one(
        "oauth.server.resource",
        required=True,
        readonly=True,
        ondelete="cascade",
        index=True,
    )
    scopes = fields.Char(readonly=True)
    redirect_uri = fields.Char(readonly=True)
    code_hash = fields.Char(readonly=True, copy=False, index=True)
    code_challenge = fields.Char(readonly=True, copy=False)
    code_expires_at = fields.Datetime(readonly=True)
    code_used = fields.Boolean(readonly=True, copy=False)
    expires_at = fields.Datetime(required=True, readonly=True)
    last_refresh = fields.Datetime(readonly=True)
    revoked = fields.Boolean(readonly=True, copy=False)
    revoked_reason = fields.Selection(
        [
            ("user", "By the user"),
            ("admin", "By an administrator"),
            ("client", "By the application"),
            ("code_reuse", "Authorization code used twice"),
            ("refresh_reuse", "Refresh token used twice"),
        ],
        readonly=True,
        copy=False,
    )
    state = fields.Selection(
        [
            ("pending", "Pending"),
            ("active", "Active"),
            ("expired", "Expired"),
            ("revoked", "Revoked"),
        ],
        compute="_compute_state",
    )
    refresh_token_ids = fields.One2many(
        "oauth.server.refresh.token", "authorization_id", readonly=True
    )

    @api.depends("revoked", "expires_at", "code_used")
    def _compute_state(self):
        now = fields.Datetime.now()
        for authorization in self:
            if authorization.revoked:
                authorization.state = "revoked"
            elif authorization.expires_at and authorization.expires_at <= now:
                authorization.state = "expired"
            elif not authorization.code_used:
                authorization.state = "pending"
            else:
                authorization.state = "active"

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    @api.model
    def _create_from_consent(
        self, user, client, resource, scopes, redirect_uri, code_challenge
    ):
        """Record an approval; returns ``(authorization, code)``."""
        code = generate_token()
        now = fields.Datetime.now()
        authorization = self.create(
            {
                "user_id": user.id,
                "client_id": client.id,
                "resource_id": resource.id,
                "scopes": scopes,
                "redirect_uri": redirect_uri,
                "code_hash": hash_token(code),
                "code_challenge": code_challenge,
                "code_expires_at": now + timedelta(seconds=CODE_LIFETIME),
                "expires_at": now + timedelta(days=resource.max_lifetime),
            }
        )
        return authorization, code

    def _revoke(self, reason):
        self.write({"revoked": True, "revoked_reason": reason})
        self.refresh_token_ids.unlink()

    def action_revoke(self):
        """Revoke from the user's preferences or the administration menu."""
        is_admin = self.env.user.has_group("base.group_system")
        for authorization in self:
            own = authorization.user_id == self.env.user
            if not own and not is_admin:
                raise AccessError(_("You can only revoke your own authorizations."))
            authorization.sudo()._revoke("user" if own else "admin")
        return True

    @api.autovacuum
    def _gc_authorizations(self):
        """Drop authorizations expired or revoked for a month, and codes
        never exchanged."""
        now = fields.Datetime.now()
        month_ago = now - timedelta(days=30)
        self.search(
            [
                "|",
                "|",
                ("expires_at", "<", month_ago),
                "&",
                ("revoked", "=", True),
                ("write_date", "<", month_ago),
                "&",
                ("code_used", "=", False),
                ("code_expires_at", "<", now - timedelta(days=1)),
            ]
        ).unlink()

    # ------------------------------------------------------------------
    # Token endpoint
    # ------------------------------------------------------------------

    @api.model
    def _exchange_code(self, client, params):
        """The authorization_code grant."""
        code = params.get("code")
        authorization = self.browse()
        if code and isinstance(code, str):
            authorization = self.search([("code_hash", "=", hash_token(code))], limit=1)
        if not authorization or authorization.client_id != client:
            raise OAuthError("invalid_grant", "Invalid authorization code.")
        if authorization.code_used:
            # the code leaked: whatever was obtained with it must stop working
            authorization._revoke("code_reuse")
            raise OAuthError("invalid_grant", "Authorization code already used.")
        if (
            authorization.revoked
            or authorization.code_expires_at <= fields.Datetime.now()
        ):
            raise OAuthError("invalid_grant", "Authorization code expired.")
        redirect_uri = params.get("redirect_uri")
        if redirect_uri and redirect_uri != authorization.redirect_uri:
            raise OAuthError("invalid_grant", "redirect_uri does not match.")
        if not check_pkce(params.get("code_verifier"), authorization.code_challenge):
            raise OAuthError("invalid_grant", "Invalid code_verifier.")
        authorization._check_resource_param(params.get("resource"))
        authorization._check_still_allowed()
        if not authorization._claim_code():
            authorization._revoke("code_reuse")
            raise OAuthError("invalid_grant", "Authorization code already used.")
        return authorization._issue_tokens(authorization.scopes)

    def _claim_code(self):
        """Mark the code used, atomically; False if it already was."""
        self.ensure_one()
        self.flush_recordset(["code_used"])
        self.env.cr.execute(
            "UPDATE oauth_server_authorization SET code_used = true "
            "WHERE id = %s AND code_used IS NOT TRUE RETURNING id",
            (self.id,),
        )
        claimed = bool(self.env.cr.fetchone())
        self.invalidate_recordset(["code_used"])
        return claimed

    @api.model
    def _refresh(self, client, params):
        """The refresh_token grant, rotating the refresh token."""
        token = self.env["oauth.server.refresh.token"]._get_by_token(
            params.get("refresh_token")
        )
        authorization = token.authorization_id
        if not token or authorization.client_id != client:
            raise OAuthError("invalid_grant", "Invalid refresh token.")
        now = fields.Datetime.now()
        if (
            authorization.revoked
            or authorization.expires_at <= now
            or token.expires_at <= now
        ):
            raise OAuthError("invalid_grant", "Refresh token expired.")
        # validate the request before using the token up
        authorization._check_resource_param(params.get("resource"))
        authorization._check_still_allowed()
        scopes = authorization._narrow_scopes(params.get("scope"))
        if not token._claim() and token.used_at < now - timedelta(
            seconds=REFRESH_REUSE_GRACE
        ):
            # someone else holds a copy of the token
            authorization._revoke("refresh_reuse")
            raise OAuthError("invalid_grant", "Refresh token already used.")
        authorization.last_refresh = now
        return authorization._issue_tokens(scopes)

    def _check_resource_param(self, resource):
        self.ensure_one()
        if resource and normalize_uri(resource) != normalize_uri(self.resource_id.uri):
            raise OAuthError(
                "invalid_target", "The resource does not match the authorization."
            )

    def _check_still_allowed(self):
        """The application, resource and user must still be allowed."""
        self.ensure_one()
        if not self._is_valid():
            raise OAuthError("invalid_grant", "The authorization is no longer valid.")

    def _is_valid(self):
        self.ensure_one()
        return (
            not self.revoked
            and self.expires_at > fields.Datetime.now()
            and self.client_id.active
            and self.resource_id.active
            and self.resource_id._is_user_allowed(self.user_id)
        )

    def _narrow_scopes(self, requested):
        """Scopes of a refreshed token: those granted, or fewer on request."""
        self.ensure_one()
        granted = (self.scopes or "").split()
        if not requested or not isinstance(requested, str):
            return " ".join(granted)
        scopes = list(dict.fromkeys(requested.split()))
        if not set(scopes) <= set(granted):
            raise OAuthError("invalid_scope", "Scopes beyond the authorization.")
        return " ".join(scopes)

    def _issue_tokens(self, scopes):
        self.ensure_one()
        access_token, expires_in = self._make_access_token(scopes)
        return {
            "access_token": access_token,
            "token_type": "Bearer",
            "expires_in": expires_in,
            "scope": scopes,
            "refresh_token": self.env["oauth.server.refresh.token"]._create_for(self),
        }

    def _make_access_token(self, scopes):
        """A JWT access token (RFC 9068) signed with the resource's validator.

        Returns ``(token, expires_in)``.
        """
        self.ensure_one()
        resource = self.resource_id
        validator = resource.jwt_validator_id.sudo()
        now = int(time.time())
        exp = min(now + resource.access_token_lifetime, _timestamp(self.expires_at))
        payload = {
            "iss": validator.issuer,
            "aud": validator.audience,
            "sub": str(self.user_id.id),
            "client_id": self.client_id.identifier,
            "scope": scopes,
            "iat": now,
            "exp": exp,
            "jti": str(uuid.uuid4()),
            "authorization_id": self.id,
        }
        token = jwt.encode(
            payload,
            validator.secret_key,
            algorithm=validator.secret_algorithm,
            headers={"typ": "at+jwt"},
        )
        return token, exp - now

    # ------------------------------------------------------------------
    # Access tokens presented to resources, revocation
    # ------------------------------------------------------------------

    @api.model
    def _get_for_access_token(self, validator, payload):
        """The authorization behind a validated access token payload.

        Refuses tokens of revoked or expired authorizations, of disabled
        applications or resources, and of users no longer allowed, so that
        revoking takes effect at once rather than when the token expires.
        """
        authorization = self.browse()
        try:
            authorization = self.browse(int(payload.get("authorization_id"))).exists()
        except (TypeError, ValueError):
            authorization = self.browse()
        if (
            not authorization
            or authorization.resource_id.jwt_validator_id != validator
            or payload.get("client_id") != authorization.client_id.identifier
            or payload.get("sub") != str(authorization.user_id.id)
            or not authorization._is_valid()
        ):
            raise UnauthorizedInvalidToken()
        return authorization

    @api.model
    def _revoke_token(self, client, token):
        """Token revocation (RFC 7009) of a refresh or access token of
        ``client``. Unknown tokens are ignored, as the RFC requires."""
        if not token or not isinstance(token, str):
            return
        refresh_token = self.env["oauth.server.refresh.token"]._get_by_token(token)
        if refresh_token:
            if refresh_token.authorization_id.client_id == client:
                refresh_token.authorization_id._revoke("client")
            return
        authorization = self._get_for_unverified_access_token(token)
        if authorization and authorization.client_id == client:
            authorization._revoke("client")

    @api.model
    def _get_for_unverified_access_token(self, token):
        try:
            claims = jwt.decode(token, options={"verify_signature": False})
        except jwt.PyJWTError:
            return self.browse()
        audience = claims.get("aud")
        resource = self.env["oauth.server.resource"]._get_by_uri(
            audience if isinstance(audience, str) else ""
        )
        if not resource:
            return self.browse()
        validator = resource.jwt_validator_id.sudo()
        try:
            payload = validator._decode(token)
            return self._get_for_access_token(validator, payload)
        except UnauthorizedInvalidToken:
            return self.browse()
