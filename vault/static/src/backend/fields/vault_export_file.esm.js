/** @odoo-module alias=vault.export.file **/
// © 2021-2024 Florian Kantelberg - initOS GmbH
// License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import {BinaryField} from "@web/views/fields/binary/binary_field";
import Exporter from "vault.export";
import VaultMixin from "vault.mixin";
import {_lt} from "@web/core/l10n/translation";
import {downloadFile} from "@web/core/network/download";
import {registry} from "@web/core/registry";
import utils from "vault.utils";

export default class VaultExportFile extends VaultMixin(BinaryField) {
    /**
     * Call the exporter and download the finalized file
     */
    async onFileDownload() {
        if (!this.props.value) {
            this.do_warn(
                _lt("Save As..."),
                _lt("The field is empty, there's nothing to save!")
            );
        } else if (utils.supported()) {
            const exporter = new Exporter();
            const content = JSON.stringify(
                await exporter.export(
                    await this._getMasterKey(),
                    this.state.fileName,
                    this.props.value
                )
            );

            const buffer = new ArrayBuffer(content.length);
            const arr = new Uint8Array(buffer);
            for (let i = 0; i < content.length; i++) arr[i] = content.charCodeAt(i);

            const blob = new Blob([arr]);
            await downloadFile(blob, this.state.fileName || "");
        }
    }
}

VaultExportFile.template = "vault.FileVaultExport";

registry.category("fields").add("vault_export_file", VaultExportFile);
