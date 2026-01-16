# Copyright 2026 Kencove (https://www.kencove.com).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AuthSessionLogoutAudit(models.Model):
    _name = "auth.session.logout.audit"
    _description = "Force Session Logout Audit Log"
    _order = "create_date desc"

    target_user_id = fields.Many2one(
        "res.users",
        string="Target User",
        ondelete="set null",
    )
    target_user_login = fields.Char(
        related="target_user_id.login",
        store=True,
    )
    request_ip = fields.Char(
        string="Request IP Address",
    )
    user_agent = fields.Char()
    status = fields.Selection(
        [
            ("success", "Success"),
            ("unauthorized", "Unauthorized"),
            ("user_not_found", "User Not Found"),
            ("error", "Error"),
        ],
        required=True,
        default="success",
    )
    error_message = fields.Text()
