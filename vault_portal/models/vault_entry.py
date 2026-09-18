# Copyright 2026 INVITU (<https://www.invitu.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, models
from odoo.exceptions import AccessError

PORTAL_WRITABLE_FIELDS = {"url", "expire_date"}


class VaultEntry(models.Model):
    _inherit = "vault.entry"

    def write(self, vals):
        if self.env.user.has_group("base.group_portal"):
            extra_fields = set(vals) - PORTAL_WRITABLE_FIELDS
            if extra_fields:
                raise AccessError(
                    _("Portal contacts may only update: %s.")
                    % ", ".join(sorted(PORTAL_WRITABLE_FIELDS))
                )
        return super().write(vals)
