# © 2026 Nitrokey GmbH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, models
from odoo.exceptions import UserError


class Vault(models.Model):
    _inherit = "vault"

    def _get_default_rights(self):
        rights = super()._get_default_rights()

        custodians = self.env.company.sudo().vault_custodian_ids
        for custodian in custodians:
            if custodian.id == self.env.uid:
                continue

            rights.append(
                (
                    0,
                    0,
                    {
                        "user_id": custodian.id,
                        "perm_create": False,
                        "perm_write": False,
                        "perm_delete": False,
                        "perm_share": True,
                    },
                )
            )

        return rights

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._enforce_custodians()
        return records

    def _enforce_custodians(self):
        custodians = self.env.company.sudo().vault_custodian_ids
        if not custodians:
            return

        required = custodians.filtered(lambda u: u.id != self.env.uid)
        for rec in self:
            custodian_rights = rec.right_ids.filtered(
                lambda r, required=required: r.user_id in required
            )
            missing = required - custodian_rights.user_id
            if missing:
                raise UserError(
                    _(
                        "The following mandatory vault custodians must be shared "
                        "with the vault and can not be removed: %s"
                    )
                    % ", ".join(missing.mapped("display_name"))
                )

            without_share = custodian_rights.filtered(lambda r: not r.perm_share)
            if without_share:
                raise UserError(
                    _(
                        "The following mandatory vault custodians must have the "
                        "share permission: %s"
                    )
                    % ", ".join(without_share.user_id.mapped("display_name"))
                )
