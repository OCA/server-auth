# © 2021 Florian Kantelberg - initOS GmbH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import json
import logging
from uuid import uuid4

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class ImportWizardPath(models.TransientModel):
    _name = "vault.import.wizard.path"
    _description = _("Import wizard path for vaults")

    name = fields.Char(required=True)
    uuid = fields.Char(required=True)


class ImportWizard(models.TransientModel):
    _name = "vault.import.wizard"
    _description = _("Import wizard for vaults")

    vault_id = fields.Many2one("vault", "Vault")
    parent_id = fields.Many2one(
        "vault.entry",
        "Parent Entry",
        domain="[('vault_id', '=', vault_id)]",
    )
    master_key = fields.Char(related="vault_id.master_key")
    name = fields.Char()
    content = fields.Binary("Database", attachment=False)
    crypted_content = fields.Char()
    uuid = fields.Char(default=lambda self: uuid4())

    path = fields.Many2one(
        "vault.import.wizard.path",
        "Path to import",
        default="",
        domain="[('uuid', '=', uuid)]",
    )

    @api.onchange("crypted_content", "content")
    def _onchange_content(self):
        for rec in self:
            if rec.crypted_content:
                for entry in json.loads(rec.crypted_content or []):
                    rec._create_path(entry)

    def _create_path(self, entry, path=None):
        self.ensure_one()
        p = f"{path} / {entry['name']}" if path else entry["name"]

        if "name" in entry:
            self.env["vault.import.wizard.path"].create({"uuid": self.uuid, "name": p})

        for child in entry.get("childs", []):
            self._create_path(child, p)

    def _import_field(self, entry, model, data):
        if not data:
            return

        # Only copy specific fields
        vals = {f: data[f] for f in ["name", "iv", "value"]}

        # Update already existing records
        domain = [("entry_id", "=", entry.id), ("name", "=", data["name"])]
        rec = model.search(domain)
        if rec:
            rec.write(vals)
        else:
            rec.create({"entry_id": entry.id, **vals})

    def _import_entry(self, entry, parent=None, path=None):
        p = f"{path} / {entry['name']}" if path else entry["name"]
        result = self.env["vault.entry"]
        if p.startswith(self.path.name or ""):
            if not parent:
                parent = self.env["vault.entry"]

            # Update existing records if already imported
            rec = self.env["vault.entry"]
            if entry.get("uuid"):
                domain = [
                    ("uuid", "=", entry["uuid"]),
                    ("vault_id", "=", self.vault_id.id),
                ]
                rec = rec.search(domain, limit=1)

            # If record not found create a new one
            vals = {f: entry.get(f) for f in ["name", "note", "url", "uuid"]}
            if not rec:
                rec = rec.create(
                    {"vault_id": self.vault_id.id, "parent_id": parent.id, **vals}
                )
            else:
                rec.write({"parent_id": parent.id, **vals})

            # Create/update the entry fields
            for field in entry.get("fields", []):
                self._import_field(rec, self.env["vault.field"], field)

            # Create/update the entry files
            for file in entry.get("files", []):
                self._import_field(rec, self.env["vault.file"], file)

            result |= rec

        else:
            rec = None

        # Create the sub-entries
        for child in entry.get("childs", []):
            result |= self._import_entry(child, rec, p)

        return result

    def action_import(self):
        self.ensure_one()

        try:
            data = json.loads(self.crypted_content)
            entries = self.env["vault.entry"]
            for entry in data:
                entries |= self.with_context(skip_log=True)._import_entry(
                    entry, self.parent_id
                )

            self.vault_id.log_entry(f"Imported entries from file {self.name}")
        except Exception as e:
            raise UserError(_("Invalid file to import from")) from e
