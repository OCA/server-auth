# Copyright 2026 INVITU (<https://www.invitu.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import json

from odoo import _
from odoo.exceptions import AccessError, UserError
from odoo.http import request, route

from odoo.addons.portal.controllers.portal import CustomerPortal


class VaultPortal(CustomerPortal):
    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        if "vault_count" in counters:
            values["vault_count"] = request.env["vault"].search_count([])
        return values

    def _vault_portal_base_values(self):
        values = self._prepare_portal_layout_values()
        values.update(
            {
                "has_keys": bool(request.env.user.active_key),
                "page_name": "vaults",
            }
        )
        return values

    def _vault_portal_searchbar_filters(self):
        return {
            "all": {"label": _("All"), "domain": []},
            "active": {"label": _("Active"), "domain": [("expired", "=", False)]},
            "expired": {"label": _("Expired"), "domain": [("expired", "=", True)]},
        }

    def _get_vault_or_404(self, vault_id):
        vault = request.env["vault"].browse(vault_id).exists()
        if not vault:
            raise request.not_found()
        try:
            vault.check_access("read")
        except AccessError:
            raise request.not_found() from None
        return vault

    def _get_vault_record(self, vault, model, record_id, label):
        record = request.env[model].browse(record_id).exists()
        if not record or record.vault_id != vault:
            raise UserError(_("%s not found in this vault.") % label)
        return record

    def _field_props(self, field):
        return {
            "id": field.id,
            "name": field.name,
            "value": field.value,
            "iv": field.iv,
            "allowedWrite": field.allowed_write,
        }

    def _file_props(self, vault_file):
        # No value/iv here: unlike fields, a file's encrypted content can
        # be sizeable, so it is only fetched on demand (download click)
        # via portal_vault_read_file, not embedded in the page's props.
        return {
            "id": vault_file.id,
            "name": vault_file.name,
            "allowedWrite": vault_file.allowed_write,
        }

    def _entry_props(self, entry):
        return {
            "id": entry.id,
            "name": entry.name,
            "url": entry.url or "",
            "expireDate": entry.expire_date
            and entry.expire_date.date().isoformat()
            or "",
            "tags": entry.tags.mapped("name"),
            "expired": entry.expired,
            "allowedWrite": entry.allowed_write,
            "allowedCreate": entry.allowed_create,
            "parentId": entry.parent_id.id or 0,
            "parentName": entry.parent_id.complete_name if entry.parent_id else "",
            "fields": [self._field_props(f) for f in entry.field_ids],
            "files": [self._file_props(f) for f in entry.file_ids],
        }

    def _vault_props(self, vault, entries):
        return {
            "vaultId": vault.id,
            "masterKey": vault.master_key or "",
            "allowedCreate": vault.allowed_create,
            "entries": [self._entry_props(e) for e in entries],
        }

    @route(["/my/vaults"], type="http", auth="user", website=True)
    def portal_my_vaults(self, **kwargs):
        values = self._vault_portal_base_values()
        values["vaults"] = request.env["vault"].search([])
        values["key_manager_props"] = json.dumps({"hasKeys": values["has_keys"]})
        return request.render("vault_portal.portal_my_vaults", values)

    @route(["/my/vaults/<int:vault_id>"], type="http", auth="user", website=True)
    def portal_vault_detail(self, vault_id, filterby=None, **kwargs):
        vault = self._get_vault_or_404(vault_id)

        searchbar_filters = self._vault_portal_searchbar_filters()
        if not filterby or filterby not in searchbar_filters:
            filterby = "all"
        domain = [("vault_id", "=", vault.id)] + searchbar_filters[filterby]["domain"]

        entries = (
            request.env["vault.entry"]
            .search(domain)
            # Hide pure organizational folders (no field of their own,
            # but with children shown as their own group) - never hide
            # a genuinely empty leaf entry (no field, no child yet),
            # which would otherwise make a freshly created entry vanish
            # with no way to add a first field to it.
            .filtered(lambda e: e.field_ids or not e.child_ids)
            .sorted(key=lambda e: (e.parent_id.id, e.complete_name))
        )

        values = self._vault_portal_base_values()
        values.update(
            {
                "vault": vault,
                "searchbar_filters": searchbar_filters,
                "filterby": filterby,
                "default_url": f"/my/vaults/{vault.id}",
                "vault_props": json.dumps(self._vault_props(vault, entries)),
            }
        )
        return request.render("vault_portal.portal_vault_detail", values)

    @route(["/my/vaults/<int:vault_id>/entries"], type="json", auth="user")
    def portal_vault_create_entry(self, vault_id, name, parent_id=0, **kwargs):
        vault = self._get_vault_or_404(vault_id)
        vals = {"vault_id": vault.id, "name": name}
        if parent_id:
            vals["parent_id"] = parent_id
        entry = request.env["vault.entry"].create(vals)
        return self._entry_props(entry)

    @route(
        ["/my/vaults/<int:vault_id>/entries/<int:entry_id>"],
        type="json",
        auth="user",
    )
    def portal_vault_write_entry(self, vault_id, entry_id, **vals):
        vault = self._get_vault_or_404(vault_id)
        entry = self._get_vault_record(vault, "vault.entry", entry_id, _("Entry"))
        entry.write(vals)
        return self._entry_props(entry)

    @route(
        ["/my/vaults/<int:vault_id>/entries/<int:entry_id>/fields"],
        type="json",
        auth="user",
    )
    def portal_vault_create_field(self, vault_id, entry_id, name, value, iv, **kwargs):
        vault = self._get_vault_or_404(vault_id)
        entry = self._get_vault_record(vault, "vault.entry", entry_id, _("Entry"))
        field = request.env["vault.field"].create(
            {"entry_id": entry.id, "name": name, "value": value, "iv": iv}
        )
        return self._field_props(field)

    @route(
        ["/my/vaults/<int:vault_id>/fields/<int:field_id>"],
        type="json",
        auth="user",
    )
    def portal_vault_write_field(self, vault_id, field_id, value, iv, **kwargs):
        vault = self._get_vault_or_404(vault_id)
        field = self._get_vault_record(vault, "vault.field", field_id, _("Field"))
        field.write({"value": value, "iv": iv})
        return self._field_props(field)

    @route(
        ["/my/vaults/<int:vault_id>/entries/<int:entry_id>/files"],
        type="json",
        auth="user",
    )
    def portal_vault_create_file(self, vault_id, entry_id, name, value, iv, **kwargs):
        vault = self._get_vault_or_404(vault_id)
        entry = self._get_vault_record(vault, "vault.entry", entry_id, _("Entry"))
        vault_file = request.env["vault.file"].create(
            {"entry_id": entry.id, "name": name, "value": value, "iv": iv}
        )
        return self._file_props(vault_file)

    @route(
        ["/my/vaults/<int:vault_id>/files/<int:file_id>/content"],
        type="json",
        auth="user",
    )
    def portal_vault_read_file(self, vault_id, file_id, **kwargs):
        vault = self._get_vault_or_404(vault_id)
        vault_file = self._get_vault_record(vault, "vault.file", file_id, _("File"))
        return {"value": vault_file.value, "iv": vault_file.iv}
