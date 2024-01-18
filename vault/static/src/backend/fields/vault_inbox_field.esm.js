/** @odoo-module alias=vault.inbox.field **/
// © 2021-2024 Florian Kantelberg - initOS GmbH
// License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import VaultField from "vault.field";
import VaultInboxMixin from "vault.inbox.mixin";
import {_lt} from "@web/core/l10n/translation";
import {registry} from "@web/core/registry";
import utils from "vault.utils";
import vault from "vault";

export default class VaultInboxField extends VaultInboxMixin(VaultField) {
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
        if (!utils.supported()) return null;

        const iv = this.props.record.data[this.props.fieldIV];
        const wrapped_key = this.props.record.data[this.props.fieldKey];

        if (!iv || !wrapped_key) return false;

        const key = await vault.unwrap(wrapped_key);
        return await utils.sym_decrypt(key, data, iv);
    }
}

VaultInboxField.defaultProps = {
    ...VaultField.defaultProps,
    fieldKey: "key",
};
VaultInboxField.displayName = _lt("Vault Inbox Field");
VaultInboxField.template = "vault.FieldVaultInbox";

registry.category("fields").add("vault_inbox_field", VaultInboxField);
