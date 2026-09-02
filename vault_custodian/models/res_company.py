# © 2026 Nitrokey GmbH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ResCompany(models.Model):
    _inherit = "res.company"

    vault_custodian_ids = fields.Many2many(
        "res.users",
        "vault_company_custodian_rel",
        "company_id",
        "user_id",
        string="Vault Custodians",
        domain=[("has_vault_key", "=", True)],
        help="Users configured here are automatically added to every newly "
        "created vault and can not be removed from it. They keep access to the "
        "end-to-end encrypted vaults, for example to recover the data in case "
        "an employee leaves the company.",
    )

    @api.constrains("vault_custodian_ids")
    def _check_vault_custodian_keys(self):
        for company in self:
            keyless = company.vault_custodian_ids.filtered(
                lambda u: not u.has_vault_key
            )
            if keyless:
                raise ValidationError(
                    _(
                        "The following users can not be vault custodians because "
                        "they have no vault keys: %s"
                    )
                    % ", ".join(keyless.mapped("display_name"))
                )
