# Copyright 2026 Kencove (https://www.kencove.com).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import ipaddress
import secrets

from odoo import api, fields, models


class AuthApiClient(models.Model):
    _name = "auth.api.client"
    _description = "API Client"

    name = fields.Char(required=True)
    whitelist_id = fields.Many2one(
        "auth.api.whitelist",
        string="Whitelist",
        required=True,
        ondelete="restrict",
    )
    secret_token = fields.Char(
        required=True,
        copy=False,
        default=lambda self: secrets.token_urlsafe(32),
    )
    active = fields.Boolean(default=True)
    token_expires_at = fields.Datetime(
        help="Leave empty for no expiration",
    )
    last_rotated = fields.Datetime()
    allowed_ips = fields.Text(
        help="Comma-separated list of allowed IPs or CIDR ranges. Empty = all allowed.",
    )
    allowed_user_ids = fields.Many2many(
        "res.users",
        string="Allowed Users",
        help="Specific users that can be impersonated.",
    )
    allowed_group_ids = fields.Many2many(
        "res.groups",
        string="Allowed Groups",
        help="User groups that can be impersonated (e.g., Portal Users).",
    )

    _sql_constraints = [
        (
            "secret_token_unique",
            "UNIQUE(secret_token)",
            "The secret token must be unique!",
        ),
    ]

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("secret_token"):
                vals["secret_token"] = secrets.token_urlsafe(32)
                vals["last_rotated"] = fields.Datetime.now()
        return super().create(vals_list)

    def action_regenerate_token(self):
        for record in self:
            record.secret_token = secrets.token_urlsafe(32)
            record.last_rotated = fields.Datetime.now()

    def is_token_expired(self):
        """Check if token has expired. Returns False if no expiry set."""
        self.ensure_one()
        if not self.token_expires_at:
            return False
        return fields.Datetime.now() > self.token_expires_at

    def is_ip_allowed(self, ip_address):
        """Check if IP address is allowed. Returns True if no restriction set."""
        self.ensure_one()
        if not self.allowed_ips:
            return True

        allowed_list = [ip.strip() for ip in self.allowed_ips.split(",") if ip.strip()]
        if not allowed_list:
            return True

        try:
            client_ip = ipaddress.ip_address(ip_address)
            for allowed in allowed_list:
                try:
                    if "/" in allowed:
                        network = ipaddress.ip_network(allowed, strict=False)
                        if client_ip in network:
                            return True
                    else:
                        if client_ip == ipaddress.ip_address(allowed):
                            return True
                except ValueError:
                    continue
            return False
        except ValueError:
            return False

    def is_user_allowed(self, user):
        """Check if user can be impersonated. Returns True if no restriction set."""
        self.ensure_one()
        # No restrictions = all users allowed
        if not self.allowed_user_ids and not self.allowed_group_ids:
            return True
        # Check if user is in allowed users list
        if self.allowed_user_ids and user in self.allowed_user_ids:
            return True
        # Check if user belongs to any allowed group
        if self.allowed_group_ids and (user.groups_id & self.allowed_group_ids):
            return True
        return False
