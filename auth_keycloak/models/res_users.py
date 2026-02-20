# Copyright 2018 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)
import logging

from odoo import _, exceptions, models

logger = logging.getLogger(__name__)


class ResUsers(models.Model):
    _inherit = "res.users"

    def button_push_to_keycloak(self):
        """Quick action to push current users to Keycloak."""
        provider = (
            self.env["auth.oauth.provider"]
            .search(
                [
                    ("enabled", "=", True),
                ]
            )
            .filtered("users_management_enabled")
        )
        enabled = len(provider) == 1
        if not enabled:
            raise exceptions.UserError(
                _("Keycloak provider not found or not configured properly.")
            )
        wiz = self.env["auth.keycloak.create.wiz"].create(
            {
                "provider_id": provider.id,
                "user_ids": [(6, 0, self.ids)],
            }
        )
        action = self.env.ref("auth_keycloak.keycloak_create_users").read()[0]
        action["res_id"] = wiz.id
        return action
