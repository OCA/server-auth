# © 2021 Florian Kantelberg - initOS GmbH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    module_vault_share = fields.Boolean()
    group_vault_export = fields.Boolean(
        "Export Vaults", implied_group="vault.group_vault_export"
    )
    group_vault_import = fields.Boolean(
        "Import Vaults", implied_group="vault.group_vault_import"
    )
    vault_custodian_ids = fields.Many2many(
        related="company_id.vault_custodian_ids",
        string="Mandatory Custodians",
        readonly=False,
    )
