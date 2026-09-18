// Copyright 2026 INVITU (<https://www.invitu.com>)
// License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import {Component, useState} from "@odoo/owl";
import {deserializeDate, serializeDate} from "@web/core/l10n/dates";
import {DateTimeInput} from "@web/core/datetime/datetime_input";
import {_t} from "@web/core/l10n/translation";
import {downloadFile} from "@web/core/network/download";
import {registry} from "@web/core/registry";
import {rpc} from "@web/core/network/rpc";
import {useService} from "@web/core/utils/hooks";

function readFileAsBase64(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result.split(",")[1]);
        reader.onerror = () => reject(reader.error);
        reader.readAsDataURL(file);
    });
}

function base64ToBlob(base64) {
    const binary = atob(base64);
    const bytes = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i++) {
        bytes[i] = binary.charCodeAt(i);
    }
    return new Blob([bytes]);
}

export class VaultDetail extends Component {
    static template = "vault_portal.VaultDetail";
    static components = {DateTimeInput};
    static props = {
        vaultId: Number,
        masterKey: String,
        allowedCreate: Boolean,
        entries: Array,
    };

    setup() {
        this.vault = useService("vault");
        this.vaultUtils = useService("vault_utils");

        // Kept for the lifetime of this page only, never persisted by
        // this module (the "vault" service itself may cache the
        // underlying private key in IndexedDB for 15 minutes, per its
        // own standard behavior).
        this.masterKey = null;

        this.state = useState({
            entries: this.props.entries.map((e) => ({
                ...e,
                fields: [...e.fields],
                files: [...e.files],
            })),
            query: "",
            revealed: {},
            fieldDrafts: {},
            fieldErrors: {},
            entryDrafts: {},
            entryErrors: {},
            newFieldDrafts: {},
            showAddField: {},
            newEntryDrafts: {},
            showAddEntry: {},
            groupErrors: {},
            fileErrors: {},
            newFileDrafts: {},
            showAddFile: {},
        });
    }

    async ensureMasterKey() {
        if (this.masterKey) {
            return this.masterKey;
        }
        this.masterKey = await this.vault.unwrap(this.props.masterKey);
        return this.masterKey;
    }

    get entryGroups() {
        const groups = new Map();
        for (const entry of this.state.entries) {
            const key = entry.parentId || 0;
            if (!groups.has(key)) {
                groups.set(key, {
                    key,
                    parentName: entry.parentName,
                    entries: [],
                });
            }
            groups.get(key).entries.push(entry);
        }
        return [...groups.values()];
    }

    get visibleEntryGroups() {
        const q = this.state.query.trim().toLowerCase();
        if (!q) {
            return this.entryGroups;
        }
        return this.entryGroups
            .map((group) => {
                const groupMatches = (group.parentName || "top level")
                    .toLowerCase()
                    .includes(q);
                const entries = group.entries.filter((entry) => {
                    if (groupMatches) {
                        return true;
                    }
                    const haystack = [entry.name, entry.url, ...entry.tags]
                        .join(" ")
                        .toLowerCase();
                    return haystack.includes(q);
                });
                return {...group, entries};
            })
            .filter((group) => group.entries.length);
    }

    isRevealed(field) {
        return field.id in this.state.revealed;
    }

    async onToggleReveal(field) {
        if (this.isRevealed(field)) {
            delete this.state.revealed[field.id];
            return;
        }

        this.state.fieldErrors[field.id] = null;
        try {
            await this.ensureMasterKey();
        } catch (err) {
            console.error(err);
            this.state.fieldErrors[field.id] = _t(
                "Unlock your vault master password first."
            );
            return;
        }

        const decrypted = await this.vaultUtils.sym_decrypt(
            this.masterKey,
            field.value,
            field.iv
        );
        this.state.revealed[field.id] =
            decrypted === null ? _t("Failed to decrypt") : decrypted;
        if (field.allowedWrite) {
            this.state.fieldDrafts[field.id] = this.state.revealed[field.id];
        }
    }

    isFieldDirty(field) {
        return (
            field.id in this.state.fieldDrafts &&
            this.state.fieldDrafts[field.id] !== this.state.revealed[field.id]
        );
    }

    async onSaveField(field) {
        this.state.fieldErrors[field.id] = null;
        const newValue = this.state.fieldDrafts[field.id];
        const iv = this.vaultUtils.generate_iv_base64();
        const encrypted = await this.vaultUtils.sym_encrypt(
            this.masterKey,
            newValue,
            iv
        );

        let result = null;
        try {
            result = await rpc(`/my/vaults/${this.props.vaultId}/fields/${field.id}`, {
                value: encrypted,
                iv,
            });
        } catch (err) {
            console.error(err);
            this.state.fieldErrors[field.id] = _t(
                "Could not save: you may not have write access to this field."
            );
            return;
        }

        field.value = result.value;
        field.iv = result.iv;
        this.state.revealed[field.id] = newValue;
    }

    showAddFieldForm(entry) {
        this.state.newFieldDrafts[entry.id] = {name: "", value: ""};
        this.state.showAddField[entry.id] = true;
    }

    async onCreateField(entry) {
        this.state.entryErrors[entry.id] = null;
        const draft = this.state.newFieldDrafts[entry.id] || {name: "", value: ""};
        if (!draft.name || !draft.value) {
            this.state.entryErrors[entry.id] = _t(
                "Please fill in both a name and a value."
            );
            return;
        }

        try {
            await this.ensureMasterKey();
        } catch (err) {
            console.error(err);
            this.state.entryErrors[entry.id] = _t(
                "Unlock your vault master password first."
            );
            return;
        }

        const iv = this.vaultUtils.generate_iv_base64();
        const encrypted = await this.vaultUtils.sym_encrypt(
            this.masterKey,
            draft.value,
            iv
        );

        let field = null;
        try {
            field = await rpc(
                `/my/vaults/${this.props.vaultId}/entries/${entry.id}/fields`,
                {name: draft.name, value: encrypted, iv}
            );
        } catch (err) {
            console.error(err);
            this.state.entryErrors[entry.id] = _t(
                "Could not add this field: you may not have permission."
            );
            return;
        }

        entry.fields.push(field);
        this.state.newFieldDrafts[entry.id] = {name: "", value: ""};
        this.state.showAddField[entry.id] = false;
    }

    async onDownloadFile(file) {
        this.state.fileErrors[file.id] = null;
        try {
            await this.ensureMasterKey();
        } catch (err) {
            console.error(err);
            this.state.fileErrors[file.id] = _t(
                "Unlock your vault master password first."
            );
            return;
        }

        let content = null;
        try {
            content = await rpc(
                `/my/vaults/${this.props.vaultId}/files/${file.id}/content`
            );
        } catch (err) {
            console.error(err);
            this.state.fileErrors[file.id] = _t(
                "Could not download: you may not have permission."
            );
            return;
        }

        const decrypted = await this.vaultUtils.sym_decrypt(
            this.masterKey,
            content.value,
            content.iv
        );
        if (decrypted === null) {
            this.state.fileErrors[file.id] = _t("Failed to decrypt.");
            return;
        }

        await downloadFile(base64ToBlob(decrypted), file.name);
    }

    showAddFileForm(entry) {
        this.state.newFileDrafts[entry.id] = {name: "", file: null};
        this.state.showAddFile[entry.id] = true;
    }

    onFileSelected(entry, ev) {
        const file = ev.target.files[0] || null;
        const draft = this.state.newFileDrafts[entry.id];
        draft.file = file;
        if (file && !draft.name) {
            draft.name = file.name;
        }
    }

    async onCreateFile(entry) {
        this.state.entryErrors[entry.id] = null;
        const draft = this.state.newFileDrafts[entry.id] || {name: "", file: null};
        if (!draft.file || !draft.name) {
            this.state.entryErrors[entry.id] = _t(
                "Please choose a file and enter a name."
            );
            return;
        }

        try {
            await this.ensureMasterKey();
        } catch (err) {
            console.error(err);
            this.state.entryErrors[entry.id] = _t(
                "Unlock your vault master password first."
            );
            return;
        }

        const base64 = await readFileAsBase64(draft.file);
        const iv = this.vaultUtils.generate_iv_base64();
        const encrypted = await this.vaultUtils.sym_encrypt(this.masterKey, base64, iv);

        let vaultFile = null;
        try {
            vaultFile = await rpc(
                `/my/vaults/${this.props.vaultId}/entries/${entry.id}/files`,
                {name: draft.name, value: encrypted, iv}
            );
        } catch (err) {
            console.error(err);
            this.state.entryErrors[entry.id] = _t(
                "Could not add this file: you may not have permission."
            );
            return;
        }

        entry.files.push(vaultFile);
        this.state.newFileDrafts[entry.id] = {name: "", file: null};
        this.state.showAddFile[entry.id] = false;
    }

    getEntryDraft(entry) {
        if (!(entry.id in this.state.entryDrafts)) {
            this.state.entryDrafts[entry.id] = {
                url: entry.url,
                expireDate: entry.expireDate,
            };
        }
        return this.state.entryDrafts[entry.id];
    }

    isEntryDirty(entry) {
        const draft = this.getEntryDraft(entry);
        return draft.url !== entry.url || draft.expireDate !== entry.expireDate;
    }

    getEntryDateTimeValue(entry) {
        const value = this.getEntryDraft(entry).expireDate;
        if (!value) {
            return false;
        }
        const dateValue = deserializeDate(value);
        return dateValue && !dateValue.invalid ? dateValue : false;
    }

    onEntryDateChange(entry, value) {
        this.getEntryDraft(entry).expireDate = value ? serializeDate(value) : "";
    }

    async onSaveEntryDetails(entry) {
        this.state.entryErrors[entry.id] = null;
        const draft = this.getEntryDraft(entry);
        const vals = {
            url: draft.url || false,
            expire_date: draft.expireDate ? `${draft.expireDate} 00:00:00` : false,
        };

        let result = null;
        try {
            result = await rpc(
                `/my/vaults/${this.props.vaultId}/entries/${entry.id}`,
                vals
            );
        } catch (err) {
            console.error(err);
            this.state.entryErrors[entry.id] = _t(
                "Could not save: you may not have write access to this entry."
            );
            return;
        }

        entry.url = result.url;
        entry.expireDate = result.expireDate;
        entry.expired = result.expired;
        this.state.entryDrafts[entry.id] = {
            url: entry.url,
            expireDate: entry.expireDate,
        };
    }

    showAddEntryForm(groupKey) {
        this.state.newEntryDrafts[groupKey] = {name: ""};
        this.state.showAddEntry[groupKey] = true;
    }

    async onCreateEntry(groupKey) {
        this.state.groupErrors[groupKey] = null;
        const draft = this.state.newEntryDrafts[groupKey] || {name: ""};
        if (!draft.name) {
            this.state.groupErrors[groupKey] = _t("Please enter a name.");
            return;
        }

        let entry = null;
        try {
            entry = await rpc(`/my/vaults/${this.props.vaultId}/entries`, {
                name: draft.name,
                parent_id: groupKey || 0,
            });
        } catch (err) {
            console.error(err);
            this.state.groupErrors[groupKey] = _t(
                "Could not add this entry: you may not have permission."
            );
            return;
        }

        entry.fields = [];
        this.state.entries.push(entry);
        this.state.newEntryDrafts[groupKey] = {name: ""};
        this.state.showAddEntry[groupKey] = false;
    }
}

registry.category("public_components").add("vault_portal.vault_detail", VaultDetail);
