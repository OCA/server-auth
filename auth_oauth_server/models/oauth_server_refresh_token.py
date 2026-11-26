# Copyright 2026 Lorenzo Battistini
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from datetime import timedelta

from odoo import api, fields, models

from ..utils import derive_token, generate_token, hash_token


class OAuthServerRefreshToken(models.Model):
    """A refresh token, stored as a digest. Each one is used once (rotation)."""

    _name = "oauth.server.refresh.token"
    _description = "OAuth Refresh Token"

    token_hash = fields.Char(required=True, readonly=True)
    authorization_id = fields.Many2one(
        "oauth.server.authorization",
        required=True,
        readonly=True,
        ondelete="cascade",
        index=True,
    )
    used_at = fields.Datetime(readonly=True)
    expires_at = fields.Datetime(required=True, readonly=True)

    _sql_constraints = [
        ("token_hash_uniq", "unique(token_hash)", "Refresh tokens must be unique."),
    ]

    @api.model
    def _create_for(self, authorization, token=None):
        """Issue a refresh token for ``authorization``; returns its value."""
        token = token or generate_token()
        lifetime = timedelta(days=authorization.resource_id.refresh_token_lifetime)
        self.create(
            {
                "token_hash": hash_token(token),
                "authorization_id": authorization.id,
                "expires_at": min(
                    fields.Datetime.now() + lifetime, authorization.expires_at
                ),
            }
        )
        return token

    @api.model
    def _get_by_token(self, token):
        if not token or not isinstance(token, str):
            return self.browse()
        return self.search([("token_hash", "=", hash_token(token))], limit=1)

    @api.model
    def _successor(self, token):
        """The refresh token issued in exchange for ``token``.

        It is derived from ``token``, so that every request presenting
        ``token`` gets the same one: concurrent requests of a client continue
        a single chain of tokens, and so does a thief holding a copy, whose
        next use then reveals the theft.
        """
        secret = self.env["ir.config_parameter"].sudo().get_param("database.secret")
        return derive_token(secret, "auth_oauth_server.refresh_token", token)

    def _claim(self):
        """Mark the token used, atomically; False if it already was.

        Of two concurrent requests presenting the token, only one updates the
        row: the other one waits, fails to serialize, and is retried by Odoo,
        which then sees the token used.
        """
        self.ensure_one()
        self.flush_recordset(["used_at"])
        self.env.cr.execute(
            "UPDATE oauth_server_refresh_token SET used_at = %s "
            "WHERE id = %s AND used_at IS NULL RETURNING id",
            (fields.Datetime.now(), self.id),
        )
        claimed = bool(self.env.cr.fetchone())
        self.invalidate_recordset(["used_at"])
        return claimed

    @api.autovacuum
    def _gc_refresh_tokens(self):
        """Drop expired tokens only: a used one presented again, however
        late, reveals a stolen copy and revokes the authorization."""
        self.search([("expires_at", "<", fields.Datetime.now())]).unlink()
