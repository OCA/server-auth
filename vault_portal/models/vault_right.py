# Copyright 2026 INVITU (<https://www.invitu.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, models
from odoo.exceptions import ValidationError


class VaultRight(models.Model):
    _inherit = "vault.right"

    def _vault_portal_mfa_policy(self):
        return (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("vault_portal.mfa_policy", "none")
        )

    @api.constrains("user_id", "perm_write", "perm_create")
    def _check_portal_mfa_policy(self):
        policy = self._vault_portal_mfa_policy()
        if policy == "none":
            return

        for right in self:
            user = right.user_id
            if not user.has_group("base.group_portal") or user.totp_enabled:
                continue

            if policy == "read":
                raise ValidationError(
                    _(
                        "%(user)s must enable two-factor authentication "
                        "before being granted any access to a vault from "
                        "the portal.",
                        user=user.display_name,
                    )
                )

            if policy == "write" and (right.perm_write or right.perm_create):
                raise ValidationError(
                    _(
                        "%(user)s must enable two-factor authentication "
                        "before being granted write or create access to a "
                        "vault from the portal.",
                        user=user.display_name,
                    )
                )
