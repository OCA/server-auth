# © 2024 Odoo Community Association (OCA)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class VaultAccessLog(models.Model):
    _name = "vault.access.log"
    _description = "Vault Access Log"
    _order = "accessed_at DESC"

    secret_id = fields.Many2one(
        "vault.entry",
        string="Secret",
        required=True,
        ondelete="cascade",
        index=True,
        help="The secret that was accessed",
    )
    user_id = fields.Many2one(
        "res.users",
        string="User",
        required=True,
        index=True,
        default=lambda self: self.env.user,
        help="The user who accessed the secret",
    )
    accessed_at = fields.Datetime(
        required=True,
        default=fields.Datetime.now,
        help="When the secret was accessed",
    )
    ip_address = fields.Char(
        string="IP Address",
        help="IP address the access originated from, resolved from the HTTP request",
    )
    access_type = fields.Selection(
        [
            ("reveal", "Reveal"),
            ("copy", "Copy"),
            ("export", "Export"),
        ],
        required=True,
        default="reveal",
        help="Type of access performed on the secret",
    )

    @api.depends("secret_id", "user_id", "access_type", "accessed_at")
    def _compute_display_name(self):
        for log in self:
            secret = log.secret_id.display_name or ""
            user = log.user_id.display_name or ""
            log.display_name = f"{secret} - {user} ({log.access_type or ''})"
