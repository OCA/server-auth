// © 2021-2024 Florian Kantelberg - initOS GmbH
// License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import {VaultField, vaultField} from "./vault_field.esm";
import VaultInboxMixin from "./vault_inbox_mixin.esm";
import {_t} from "@web/core/l10n/translation";
import {registry} from "@web/core/registry";

export class VaultInboxField extends VaultInboxMixin(VaultField) {
    static defaultProps = {
        ...VaultField.defaultProps,
        fieldKey: "key",
    };
    static template = "vault.FieldVaultInbox";
    /**
     * Save the content in an entry of a vault
     *
     * @private
     */
    async _onSaveValue() {
        await this.saveValue("vault.field", this.props.value);
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

export const vaultInboxField = {
    ...vaultField,
    component: VaultInboxField,
    displayName: _t("Vault Inbox Field"),
};

registry.category("fields").add("vault_inbox_field", vaultInboxField);
