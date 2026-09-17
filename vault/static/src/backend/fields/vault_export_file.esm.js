// © 2021-2024 Florian Kantelberg - initOS GmbH
// License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import {BinaryField, binaryField} from "@web/views/fields/binary/binary_field";
import VaultMixin from "./vault_mixin.esm";
import {_t} from "@web/core/l10n/translation";
import {downloadFile} from "@web/core/network/download";
import {registry} from "@web/core/registry";
import {useService} from "@web/core/utils/hooks";

export class VaultExportFile extends VaultMixin(BinaryField) {
    static template = "vault.FileVaultExport";
    setup() {
        super.setup();
        this.exporter = useService("vault_export");
        this.vault_utils = useService("vault_utils");
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
     * Call the exporter and download the finalized file
     */
    async onFileDownload() {
        const cryptedValue = await this._getCryptedValue();
        if (!cryptedValue) {
            this.notification.add(_t("The field is empty, there's nothing to save!"), {
                title: _t("Save As..."),
                type: "danger",
            });
        } else if (this.vault_utils.supported()) {
            const content = JSON.stringify(
                await this.exporter.export(
                    await this._getMasterKey(),
                    this.fileName,
                    cryptedValue
                )
            );

            const buffer = new ArrayBuffer(content.length);
            const arr = new Uint8Array(buffer);
            for (let i = 0; i < content.length; i++) arr[i] = content.charCodeAt(i);

            const blob = new Blob([arr]);
            await downloadFile(blob, this.fileName || "");
        }
    }
}

export const vaultExportFileField = {
    ...binaryField,
    component: VaultExportFile,
    displayName: _t("Vault export file"),
};

registry.category("fields").add("vault_export_file", vaultExportFileField);
