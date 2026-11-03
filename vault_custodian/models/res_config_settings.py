# © 2026 Nitrokey GmbH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    vault_custodian_ids = fields.Many2many(
        related="company_id.vault_custodian_ids",
        string="Mandatory Custodians",
        readonly=False,
    )
