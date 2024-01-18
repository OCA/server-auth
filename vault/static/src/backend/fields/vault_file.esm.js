/** @odoo-module alias=vault.file **/
// © 2021-2024 Florian Kantelberg - initOS GmbH
// License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import {BinaryField} from "@web/views/fields/binary/binary_field";
import VaultMixin from "vault.mixin";
import {_lt} from "@web/core/l10n/translation";
import {downloadFile} from "@web/core/network/download";
import {registry} from "@web/core/registry";
import {useService} from "@web/core/utils/hooks";
import utils from "vault.utils";

export default class VaultFile extends VaultMixin(BinaryField) {
    setup() {
        super.setup();

        this.action = useService("action");
    }

    async update({data, name}) {
        const encrypted = await this._encrypt(data);
        return await super.update({data: encrypted, name: name});
    }

    /**
     * Send the secret to an inbox of an user
     *
     * @param {Object} ev
     */
    async _onSendValue(ev) {
        ev.stopPropagation();

        await this.sendValue("", this.props.value, this.state.fileName);
    }

    /**
     * Decrypt the file and download it
     */
    async onFileDownload() {
        if (!this.props.value) {
            this.do_warn(
                _lt("Save As..."),
                _lt("The field is empty, there's nothing to save!")
            );
        } else if (utils.supported()) {
            const decrypted = await this._decrypt(this.props.value);
            const base64 = atob(decrypted);
            const buffer = new ArrayBuffer(base64.length);
            const arr = new Uint8Array(buffer);
            for (let i = 0; i < base64.length; i++) arr[i] = base64.charCodeAt(i);

            const blob = new Blob([arr]);
            await downloadFile(blob, this.state.fileName || "");
        }
    }
}

VaultFile.displayName = _lt("Vault File");
VaultFile.template = "vault.FileVault";

registry.category("fields").add("vault_file", VaultFile);
