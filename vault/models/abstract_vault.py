# © 2021 Florian Kantelberg - initOS GmbH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import _, api, fields, models
from odoo.exceptions import AccessError

_logger = logging.getLogger(__name__)


class VaultLog(models.Model):
    _name = "vault.log"
    _description = _("Log entry of a vault")
    _order = "create_date DESC"
    _rec_name = "message"

    def _get_log_state(self):
        return [
            ("info", _("Information")),
            ("warn", _("Warning")),
            ("error", _("Error")),
        ]

    vault_id = fields.Many2one(
        "vault",
        "Vault",
        ondelete="cascade",
        required=True,
        readonly=True,
    )
    entry_id = fields.Many2one(
        "vault.entry",
        "Entry",
        ondelete="cascade",
        readonly=True,
    )
    user_id = fields.Many2one("res.users", "User", required=True, readonly=True)
    state = fields.Selection(_get_log_state, readonly=True)
    message = fields.Char(readonly=True, required=True)

    @api.model
    def create(self, values):
        res = super().create(values)
        if not self.env.context.get("skip_log", False):
            _logger.info("Vault log: %s", res.message)
        return res


class AbstractVault(models.AbstractModel):
    """Models must have the following fields:
    `perm_user`: The permissions are computed for this user
    `allowed_write`: The current user can read from the vault
    `allowed_write`: The current user has write access to the vault
    `allowed_share`: The current user can share the vault with other users
    `allowed_delete`: The current user can delete the vault or entries of it
    """

    _name = "vault.abstract"
    _description = _("Abstract model to implement general access rights")

    @api.model
    def raise_access_error(self):
        raise AccessError(
            _(
                "The requested operation can not be completed due to security "
                "restrictions."
            )
        )

    def check_access_rule(self, operation):
        super().check_access_rule(operation)

        if self.env.su:
            return

        # We have to recompute if the user of the environment changed
        if self.env.user != self.mapped("perm_user"):
            vault = self if self._name == "vault" else self.mapped("vault_id")
            vault._compute_access()

        # Check the operation and matching permissions
        if operation == "read" and not self.filtered("allowed_read"):
            self.raise_access_error()

        if operation == "write" and not self.filtered("allowed_write"):
            self.raise_access_error()

        if operation == "unlink" and not self.filtered("allowed_delete"):
            self.raise_access_error()

    def _log_entry(self, msg, state):
        raise NotImplementedError()

    def log_entry(self, msg):
        return self._log_entry(msg, None)

    def log_info(self, msg):
        return self._log_entry(msg, "info")

    def log_warn(self, msg):
        return self._log_entry(msg, "warn")

    def log_error(self, msg):
        return self._log_entry(msg, "error")
