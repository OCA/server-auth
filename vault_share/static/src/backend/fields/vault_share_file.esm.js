// © 2021-2024 Florian Kantelberg - initOS GmbH
// License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import {VaultFile, vaultFileField} from "@vault/backend/fields/vault_file.esm";
import VaultShareMixin from "./vault_share_mixin.esm";
import {_t} from "@web/core/l10n/translation";
import {binaryFieldProps} from "@web/views/fields/binary/binary_field";
import {getContent} from "@vault/backend/fields/vault_mixin.esm";
import {registry} from "@web/core/registry";

export class VaultShareFile extends VaultShareMixin(VaultFile, binaryFieldProps) {
    static template = "vault.FileShareVault";

    /**
     * The secret file of a share is stored in a char field. Store the encrypted
     * content as plain string instead of the binary payload of the BinaryField.
     *
     * @param {Object} file
     */
    async update({data, name}) {
        const {fileNameField, record} = this.props;
        const changes = {
            [this.props.name]: data ? await this._encrypt(data) : false,
        };
        if (fileNameField && fileNameField in record.fields)
            changes[fileNameField] = (data && name) || "";
        return await record.update(changes);
    }

    /**
     * The encrypted content is already loaded in the record
     */
    async _getCryptedValue() {
        return getContent(this.value);
    }
}

export const vaultShareFileField = {
    ...vaultFileField,
    component: VaultShareFile,
    displayName: _t("Vault Share Field"),
    supportedTypes: ["char"],
};

registry.category("fields").add("vault_share_file", vaultShareFileField);
