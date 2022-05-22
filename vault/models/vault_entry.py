# © 2021 Florian Kantelberg - initOS GmbH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from datetime import datetime
from uuid import uuid4

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)


class VaultEntry(models.Model):
    _name = "vault.entry"
    _description = _("Entry inside a vault")
    _inherit = ["vault.abstract"]
    _order = "complete_name"
    _rec_name = "complete_name"

    parent_id = fields.Many2one("vault.entry", "Parent", ondelete="cascade")
    child_ids = fields.One2many("vault.entry", "parent_id", "Child")

    vault_id = fields.Many2one("vault", "Vault", ondelete="cascade", required=True)
    user_id = fields.Many2one(related="vault_id.user_id")
    field_ids = fields.One2many("vault.field", "entry_id", "Fields")
    file_ids = fields.One2many("vault.file", "entry_id", "Files")
    log_ids = fields.One2many("vault.log", "entry_id", "Log", readonly=True)

    perm_user = fields.Many2one(related="vault_id.perm_user", store=False)
    allowed_read = fields.Boolean(related="vault_id.allowed_read", store=False)
    allowed_share = fields.Boolean(related="vault_id.allowed_share", store=False)
    allowed_write = fields.Boolean(related="vault_id.allowed_write", store=False)
    allowed_delete = fields.Boolean(related="vault_id.allowed_delete", store=False)

    complete_name = fields.Char(
        compute="_compute_complete_name",
        store=True,
        readonly=True,
    )
    uuid = fields.Char(default=lambda self: uuid4(), required=True)
    name = fields.Char(required=True)
    url = fields.Char()
    note = fields.Text()
    tags = fields.Many2many("vault.tag")
    expire_date = fields.Datetime("Expires on", default=False)
    expired = fields.Boolean(compute="_compute_expired", store=False)

    _sql_constraints = [
        ("vault_uuid_uniq", "UNIQUE(vault_id, uuid)", _("The UUID must be unique.")),
    ]

    @api.depends("name", "parent_id.complete_name")
    def _compute_complete_name(self):
        for rec in self:
            if rec.parent_id:
                rec.complete_name = f"{rec.parent_id.complete_name} / {rec.name}"
            else:
                rec.complete_name = rec.name

    @api.depends("expire_date")
    def _compute_expired(self):
        now = datetime.now()
        for rec in self:
            rec.expired = rec.expire_date and now > rec.expire_date

    def log_change(self, action):
        self.ensure_one()
        self.log_info(
            f"{action} entry {self.complete_name} by {self.env.user.display_name}"
        )

    @api.model_create_single
    def create(self, values):
        res = super().create(values)
        res.log_change("Created")
        return res

    def unlink(self):
        for rec in self:
            rec.log_change("Deleted")

        return super().unlink()

    def _log_entry(self, msg, state):
        self.ensure_one()
        return (
            self.env["vault.log"]
            .sudo()
            .create(
                {
                    "vault_id": self.vault_id.id,
                    "entry_id": self.id,
                    "user_id": self.env.uid,
                    "message": msg,
                    "state": state,
                }
            )
        )

    def action_open_import_wizard(self):
        self.ensure_one()
        wizard = self.env.ref("vault.view_vault_import_wizard")
        return {
            "name": _("Import from file"),
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": "vault.import.wizard",
            "views": [(wizard.id, "form")],
            "view_id": wizard.id,
            "target": "new",
            "context": {
                "default_vault_id": self.vault_id.id,
                "default_parent_id": self.id,
            },
        }

    def action_open_export_wizard(self):
        self.ensure_one()
        wizard = self.env.ref("vault.view_vault_export_wizard")
        return {
            "name": _("Export to file"),
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": "vault.export.wizard",
            "views": [(wizard.id, "form")],
            "view_id": wizard.id,
            "target": "new",
            "context": {
                "default_vault_id": self.vault_id.id,
                "default_entry_id": self.id,
            },
        }
