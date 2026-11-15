# © 2021 Florian Kantelberg - initOS GmbH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class VaultLog(models.Model):
    _name = "vault.log"
    _description = "Log entry of a vault"
    _order = "create_date DESC"
    _rec_name = "message"

    vault_id = fields.Many2one(
        "vault",
        ondelete="cascade",
        required=True,
        readonly=True,
    )
    entry_id = fields.Many2one(
        "vault.entry",
        ondelete="cascade",
        readonly=True,
    )
    user_id = fields.Many2one("res.users", required=True, readonly=True)
    state = fields.Selection(lambda self: self._get_log_state(), readonly=True)
    message = fields.Char(readonly=True, required=True)

    def _get_log_state(self):
        return [
            ("info", self.env._("Information")),
            ("warn", self.env._("Warning")),
            ("error", self.env._("Error")),
        ]

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        if not self.env.context.get("skip_log", False):
            _logger.info("Vault log: %s", res.message)
        return res
