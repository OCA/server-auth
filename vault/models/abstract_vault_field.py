# © 2021 Florian Kantelberg - initOS GmbH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class AbstractVaultField(models.AbstractModel):
    _name = "vault.abstract.field"
    _description = "Abstract model to implement basic fields for encryption"

    entry_id = fields.Many2one("vault.entry", ondelete="cascade", required=True)
    entry_name = fields.Char(related="entry_id.complete_name")
    vault_id = fields.Many2one(related="entry_id.vault_id")
    master_key = fields.Char(compute="_compute_master_key", store=False)

    perm_user = fields.Many2one(related="vault_id.perm_user", store=False)
    allowed_read = fields.Boolean(related="vault_id.allowed_read", store=False)
    allowed_create = fields.Boolean(related="vault_id.allowed_create", store=False)
    allowed_write = fields.Boolean(related="vault_id.allowed_write", store=False)
    allowed_share = fields.Boolean(related="vault_id.allowed_share", store=False)
    allowed_delete = fields.Boolean(related="vault_id.allowed_delete", store=False)

    name = fields.Char(required=True)
    iv = fields.Char()

    @api.depends("entry_id.vault_id.master_key")
    def _compute_master_key(self):
        for rec in self:
            rec.master_key = rec.vault_id.master_key

    def log_change(self, action):
        if self.env.context.get("vault_skip_log"):
            return

        for rec in self:
            rec.entry_id.log_info(
                f"{action} value {rec.name} of {rec.entry_id.complete_name} "
                f"by {self.env.user.display_name}"
            )

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        res.log_change("Created")
        return res

    def unlink(self):
        self.log_change("Deleted")
        return super().unlink()

    def write(self, values):
        self.log_change("Changed")
        return super().write(values)
