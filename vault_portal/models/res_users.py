# Copyright 2026 INVITU (<https://www.invitu.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class ResUsers(models.Model):
    _inherit = "res.users"

    def write(self, vals):
        users = self.env["res.users"]
        if "totp_secret" in vals and not vals["totp_secret"]:
            users = self.filtered("totp_enabled")

        res = super().write(vals)

        if users:
            users._vault_portal_apply_mfa_disable_policy()

        return res

    def _vault_portal_apply_mfa_disable_policy(self):
        policy = self.env["vault.right"]._vault_portal_mfa_policy()
        if policy == "none":
            return

        portal_users = self.filtered(lambda u: u.has_group("base.group_portal"))
        if not portal_users:
            return

        rights = (
            self.env["vault.right"].sudo().search([("user_id", "in", portal_users.ids)])
        )
        if policy == "read":
            rights.unlink()
        elif policy == "write":
            rights.filtered(lambda r: r.perm_write or r.perm_create).write(
                {"perm_write": False, "perm_create": False}
            )
