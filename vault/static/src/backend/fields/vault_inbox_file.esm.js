// © 2021-2024 Florian Kantelberg - initOS GmbH
// License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import {t, useProps} from "@odoo/owl";
import {VaultFile, vaultFileField} from "./vault_file.esm";
import VaultInboxMixin from "./vault_inbox_mixin.esm";
import {binaryFieldProps} from "@web/views/fields/binary/binary_field";
import {getContent, vaultMixinProps} from "./vault_mixin.esm";
import {_t} from "@web/core/l10n/translation";
import {registry} from "@web/core/registry";

export class VaultInboxFile extends VaultInboxMixin(VaultFile) {
    static template = "vault.FileVaultInbox";
    props = useProps({
        ...binaryFieldProps,
        ...vaultMixinProps,
        fieldKey: t.string().optional("key"),
    });

    get value() {
        return getContent(this.props.record.data[this.props.name]);
    }

    /**
     * Save the content in an entry of a vault
     *
     * @private
     */
    async _onSaveValue() {
        await this.saveValue("vault.file", this.value, this.fileName);
    }

    /**
     * Decrypt the data with the private key of the vault
     *
     * @private
     * @param {String} data
     * @returns the decrypted data
     */
    async _decrypt(data) {
        if (!this.vault_utils.supported()) return null;

        const iv = this.props.record.data[this.props.fieldIV];
        const wrapped_key = this.props.record.data[this.props.fieldKey];

        if (!iv || !wrapped_key) return false;

        const key = await this.vault.unwrap(wrapped_key);
        return await this.vault_utils.sym_decrypt(key, data, iv);
    }
}

const vaultInboxFileField = {
    ...vaultFileField,
    component: VaultInboxFile,
    displayName: _t("Vault Inbox File"),
};

registry.category("fields").add("vault_inbox_file", vaultInboxFileField);
