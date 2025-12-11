# © 2021 Florian Kantelberg - initOS GmbH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import json
import logging
from datetime import datetime

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class ExportWizard(models.TransientModel):
    _name = "vault.export.wizard"
    _description = "Export wizard for vaults"

    vault_id = fields.Many2one("vault", "Vault")
    entry_id = fields.Many2one(
        "vault.entry", "Entries", domain="[('vault_id', '=', vault_id)]"
    )
    master_key = fields.Char(related="vault_id.master_key")
    name = fields.Char(default=lambda self: self._default_name())
    content = fields.Binary("Download", attachment=False)
    include_childs = fields.Boolean(default=True)

    @api.onchange("vault_id", "entry_id")
    def _onchange_content(self):
        for rec in self.with_context(skip_log=True):
            rec.content = self._export_content(
                rec.vault_id,
                rec.entry_id,
                rec.include_childs,
            )

    def _default_name(self):
        return datetime.now().strftime("database-%Y%m%d-%H%M.json")

    def _export_content(self, vault=None, entry=None, include_childs=False):
        if entry:
            entries = entry
        elif vault:
            entries = vault.entry_ids.filtered_domain([("parent_id", "=", False)])
        else:
            return json.dumps([])

        data = [self._export_entry(x, include_childs) for x in entries]
        return json.dumps(data)

    @api.model
    def _export_field(self, rec):
        def ensure_string(x):
            return x.decode() if isinstance(x, bytes) else x

        return {f: ensure_string(rec[f]) for f in ["name", "iv", "value"]}

    @api.model
    def _export_entry(self, entry, include_childs=False):
        if include_childs:
            childs = [self._export_entry(x, include_childs) for x in entry.child_ids]
        else:
            childs = []

        return {
            "uuid": entry.uuid,
            "name": entry.name,
            "note": entry.note,
            "url": entry.url,
            "fields": entry.field_ids.mapped(self._export_field),
            "files": entry.file_ids.mapped(self._export_field),
            "childs": childs,
        }
