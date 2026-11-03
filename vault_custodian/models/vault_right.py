# © 2026 Nitrokey GmbH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, models
from odoo.exceptions import UserError


class VaultRight(models.Model):
    _inherit = "vault.right"

    def _filtered_custodians(self):
        custodians = self.env.company.sudo().vault_custodian_ids
        return self.filtered(lambda r: r.user_id in custodians)

    def write(self, values):
        # Prevent revoking the share with a mandatory custodian
        if not self.env.su and self._filtered_custodians():
            if values.get("perm_share") is False:
                raise UserError(
                    _("The share permission of a custodian can not be removed.")
                )
            if "user_id" in values:
                raise UserError(_("The user of a custodian can not be changed."))

        return super().write(values)

    def unlink(self):
        if not self.env.su and self._filtered_custodians():
            raise UserError(
                _("A mandatory custodian can not be removed from the vault.")
            )

        return super().unlink()
