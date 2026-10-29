# © 2021 Florian Kantelberg - initOS GmbH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from uuid import uuid4

from odoo import api, fields, models
from odoo.exceptions import AccessError

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
    # The token gives write access to the inbox of the user
    inbox_token = fields.Char(
        default=lambda self: uuid4(),
        readonly=True,
        groups="base.group_erp_manager",
    )

    @api.depends("keys", "keys.current")
    def _compute_active_key(self):
        for rec in self:
            keys = rec.sudo().keys.filtered("current")
            rec.active_key = keys[0] if keys else None

    def _can_manage_vault_of(self, user):
        """Only the user itself or user administrators can manage the vault
        settings of an user"""
        return (
            self.env.su
            or user == self.env.user
            or self.env.user.has_group("base.group_erp_manager")
        )

    @api.depends("inbox_token")
    @api.depends_context("uid")
    def _compute_inbox_link(self):
        base_url = self.env["ir.config_parameter"].sudo().get_str("web.base.url")
        for rec in self:
            if self._can_manage_vault_of(rec._origin):
                rec.inbox_link = f"{base_url}/vault/inbox/{rec.sudo().inbox_token}"
            else:
                rec.inbox_link = False

    @api.model
    def action_get_vault(self):
        result = self.env["ir.actions.act_window"]._for_xml_id(
            "vault.action_res_users_keys"
        )
        result["res_id"] = self.env.uid
        return result

    def action_new_inbox_token(self):
        self.ensure_one()
        if not self._can_manage_vault_of(self):
            raise AccessError(self.env._("You can't change the inbox of other users."))
        self.sudo().inbox_token = uuid4()
        return self.action_get_vault()

    def action_invalidate_key(self):
        """Disable the current key and remove all accesses to the vaults"""
        self.ensure_one()
        if not self.env.su and self != self.env.user:
            raise AccessError(
                self.env._("You can't invalidate the key of other users.")
            )
        self.keys.write({"current": False})
        self.vault_right_ids.sudo().unlink()
        self.inbox_ids.unlink()
        self.env["vault"].search([])._compute_access()  # pylint: disable=no-search-all
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
