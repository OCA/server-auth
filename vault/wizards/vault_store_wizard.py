# © 2021 Florian Kantelberg - initOS GmbH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class VaultStoreWizard(models.TransientModel):
    _name = "vault.store.wizard"
    _description = "Wizard store a shared secret in a vault"

    vault_id = fields.Many2one("vault", required=True)
    entry_id = fields.Many2one(
        "vault.entry",
        domain="[('vault_id', '=', vault_id)]",
        required=True,
    )
    model = fields.Char(required=True)
    master_key = fields.Char(compute="_compute_master_key", store=False)
    name = fields.Char(required=True)
    iv = fields.Char(required=True)
    key = fields.Char(required=True)
    secret = fields.Char(required=True)
    secret_temporary = fields.Char(required=True)

    @api.depends("entry_id", "vault_id")
    def _compute_master_key(self):
        for rec in self:
            rec.master_key = rec.vault_id.master_key

    def action_store(self):
        self.ensure_one()
        if self.model not in ("vault.field", "vault.file"):
            raise UserError(self.env._("Invalid model to store the secret"))

        self.env[self.model].create(
            {
                "entry_id": self.entry_id.id,
                "name": self.name,
                "iv": self.iv,
                "value": self.secret,
            }
        )
