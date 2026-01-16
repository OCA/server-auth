# Copyright 2026 Kencove (https://www.kencove.com).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import secrets

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    auth_session_logout_token = fields.Char(
        string="Force Logout Token",
        config_parameter="auth_session_logout_api.token",
        help="Secure token used to authenticate force logout API requests",
    )

    def action_generate_token(self):
        """Generate a new secure token"""
        new_token = secrets.token_urlsafe(32)
        self.env["ir.config_parameter"].sudo().set_param(
            "auth_session_logout_api.token", new_token
        )
        self.auth_session_logout_token = new_token
        return True
