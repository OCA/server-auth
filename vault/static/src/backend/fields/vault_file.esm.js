// © 2021-2024 Florian Kantelberg - initOS GmbH
// License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import {BinaryField, binaryField} from "@web/views/fields/binary/binary_field";
import VaultMixin from "./vault_mixin.esm";
import {_t} from "@web/core/l10n/translation";
import {downloadFile} from "@web/core/network/download";
import {registry} from "@web/core/registry";
import {useService} from "@web/core/utils/hooks";

export class VaultFile extends VaultMixin(BinaryField) {
    static template = "vault.FileVault";
    setup() {
        super.setup();
        this.orm = useService("orm");
        this.notification = useService("notification");
        this.action = useService("action");
    }

    async update({data, name}) {
        const encrypted = await this._encrypt(data);
        return await super.update({data: encrypted, name: name});
    }

    /**
     * Get the value saved on db because the system is showing just the
     * size on the props.
     *
     * @param {Object} ev
     */
    async _getCryptedValue() {
        const crypted = await this.orm.read(
            this.props.record.resModel,
            [this.props.record.resId],
            [this.props.name]
        );
        return crypted[0][this.props.name];
    }

    /**
     * Send the secret to an inbox of an user
     *
     * @param {Object} ev
     */
    async _onSendValue(ev) {
        ev.stopPropagation();

        await this.sendValue("", await this._getCryptedValue(), this.fileName);
    }

    /**
     * Decrypt the file and download it
     */
    async onFileDownload() {
        const cryptedValue = await this._getCryptedValue();
        if (!cryptedValue) {
            this.notification.add(_t("The field is empty, there's nothing to save!"), {
                title: _t("Save As..."),
                type: "danger",
            });
        } else if (this.vault_utils.supported()) {
            const decrypted = await this._decrypt(cryptedValue);
            const base64 = atob(decrypted);
            const buffer = new ArrayBuffer(base64.length);
            const arr = new Uint8Array(buffer);
            for (let i = 0; i < base64.length; i++) arr[i] = base64.charCodeAt(i);

            const blob = new Blob([arr]);
            await downloadFile(blob, this.fileName || "");
        }
    }
}

export const vaultFileField = {
    ...binaryField,
    component: VaultFile,
    displayName: _t("Vault File"),
};

registry.category("fields").add("vault_file", vaultFileField);
