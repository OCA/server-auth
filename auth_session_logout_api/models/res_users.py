# Copyright 2026 Kencove (https://www.kencove.com).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import uuid

from odoo import _, api, fields, models
from odoo.exceptions import AccessError


class ResUsers(models.Model):
    _inherit = "res.users"

    session_logout_key = fields.Char(
        copy=False,
        help="Random key included in session token computation. "
        "Changing this value invalidates all existing sessions for the user.",
    )
    force_logout_count = fields.Integer(
        help="Number of times this user has been force logged out",
        default=0,
        copy=False,
    )

    @api.model
    def _get_session_token_fields(self):
        """Add session_logout_key to session token computation."""
        return super()._get_session_token_fields() | {"session_logout_key"}

    def action_force_logout(self):
        """Force logout all user sessions by changing session_logout_key.

        Only users with Administration/Settings group can call this method.
        External systems should use the API endpoint with token authentication.
        """
        self.ensure_one()
        if not self.env.context.get("auth_session_logout_api_call", False):
            user = self.env["res.users"].browse(self.env.uid)
            if not user.has_group("base.group_system"):
                raise AccessError(_("Only administrators can force logout users."))

        # Generate new random key to invalidate all existing sessions
        new_key = uuid.uuid4().hex
        self.sudo().write(
            {
                "session_logout_key": new_key,
                "force_logout_count": self.force_logout_count + 1,
            }
        )
        return True
