# © 2021 Florian Kantelberg - initOS GmbH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from uuid import uuid4

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class ResUsers(models.Model):
    _inherit = "res.users"

    active_key = fields.Many2one(
        "res.users.key",
        compute="_compute_active_key",
        store=False,
    )
    keys = fields.One2many("res.users.key", "user_id", readonly=True)
    vault_right_ids = fields.One2many("vault.right", "user_id", readonly=True)
    inbox_ids = fields.One2many("vault.inbox", "user_id")
    inbox_enabled = fields.Boolean(default=True)
    inbox_link = fields.Char(compute="_compute_inbox_link", readonly=True, store=False)
    inbox_token = fields.Char(default=lambda self: uuid4(), readonly=True)

    @api.depends("keys", "keys.current")
    def _compute_active_key(self):
        for rec in self:
            keys = rec.keys.filtered("current")
            rec.active_key = keys[0] if keys else None

    @api.depends("inbox_token")
    def _compute_inbox_link(self):
        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        for rec in self:
            rec.inbox_link = f"{base_url}/vault/inbox/{rec.inbox_token}"

    @api.model
    def action_get_vault(self):
        action = self.sudo().env.ref("vault.action_res_users_keys")
        result = action.read()[0]
        result["res_id"] = self.env.uid
        return result

    def action_new_inbox_token(self):
        self.ensure_one()
        self.sudo().inbox_token = uuid4()
        return self.action_get_vault()

    def action_invalidate_key(self):
        """Disable the current key and remove all accesses to the vaults"""
        self.ensure_one()
        self.keys.write({"current": False})
        self.vault_right_ids.sudo().unlink()
        self.inbox_ids.unlink()
        self.env["vault"].search([])._compute_access()
        return self.action_get_vault()

    @api.model
    def find_user_of_inbox(self, token):
        return self.search([("inbox_token", "=", token), ("inbox_enabled", "=", True)])

    def get_vault_keys(self):
        self.ensure_one()

        if not self.active_key:
            return {}

        return {
            "iterations": self.active_key.iterations,
            "iv": self.active_key.iv,
            "private": self.active_key.private,
            "public": self.active_key.public,
            "salt": self.active_key.salt,
            "uuid": self.active_key.uuid,
            "version": self.active_key.version,
        }
