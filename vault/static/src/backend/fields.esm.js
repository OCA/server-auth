/** @odoo-module alias=vault.fields **/

import { registry } from "@web/core/registry";
import { _lt } from "@web/core/l10n/translation";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import vault  from "vault";
import { supported, generate_pass, sym_encrypt, sym_decrypt, generate_iv_base64, generate_key } from 'vault.utils';
import { useService } from "@web/core/utils/hooks";
import { Component, useState, useRef, useEffect, onWillUpdateProps } from "@odoo/owl";
import { FileUploader } from "@web/views/fields/file_handler";
import { isBinarySize } from "@web/core/utils/binary";
import { download } from "@web/core/network/download";


class VaultAbstract extends Component {
    setup() {
        super.setup(...arguments);
        this.notification = useService("notification");
        this.action = useService("action");
    }
    get supported() {
        return supported();
    }
    
    async onChange(value) {
        console.log(value)
        if (this.supported) {
            let data = await this._encrypt(value);
            console.log(data)
            this.props.update(data);
        }
    }
    
    /**
     * Toggle if the value is shown or hidden, and decrypt the value if shown
     *
     * @private
     * @param {OdooEvent} ev
     */
    async _onShowValue(ev) {
        console.log(this)
        ev.stopPropagation();

        this.state.decrypted = !this.state.decrypted;
        this.state.show = !this.state.decrypted;
        if (this.state.decrypted) this.state.decrypted_value = await this._decrypt(this.props.value);
        else this.state.decrypted_value = false;

        console.log(this.state)
    }

     /**
         * Copy the decrypted value to the clipboard
         *
         * @private
         * @param {OdooEvent} ev
         */
    async _onCopyValue(ev) {
        ev.stopPropagation();

        const value = await this._decrypt(this.value);
        await navigator.clipboard.writeText(value);

        this.notification.add(
            this.env._t("Value copied."),
            {
                title: this.env._t("Clipboard"),
                type: "success",
            },
        );
    }
    /**
         * Send the value with an internal user
         *
         * @private
         * @param {OdooEvent} ev
         */
    async _onSendValue(ev) {
        ev.stopPropagation();

        const key = await generate_key();
        const iv = generate_iv_base64();
        const value = await this._decrypt(this.value);

        this.action.doAction({
            type: "ir.actions.act_window",
            title: this.env._t("Send the secret to another user"),
            target: "new",
            res_model: "vault.send.wizard",
            views: [[false, "form"]],
            context: {
                default_secret: await sym_encrypt(key, value, iv),
                default_iv: iv,
                default_key: await vault.wrap(key),
            },
        });
    }

    /**
         * Extract the IV or generate a new one if needed
         *
         * @returns the IV to use
         */
    _getIV() {
        console.log(this)
        if (!supported()) return null;

        // IV already read. Reuse it
        if (this.state.iv) return this.state.iv;

        // Read the IV from the field
        this.state.iv = this.props.record.data[this.props.field_iv];
        if (this.state.iv) return this.state.iv;

        // Generate a new IV
        this.state.iv = generate_iv_base64();
        this.props.record.update({
            [this.props.field_iv]: this.state.iv
        })
        return this.state.iv;
    }

    /**
     * Extract the master key of the vault or generate a new one
     *
     * @returns the master key to use
     */
    async _getMasterKey() {
        if (!supported()) return null;

        // Check if the master key is already extracted
        if (this.state.key) return await vault.unwrap(this.state.key);

        // Get the wrapped master key from the field
        this.state.key = this.props.record.data[this.props.field_key];
        if (this.state.key) return await vault.unwrap(this.state.key);

        // Generate a new master key and write it to the field
        const key = await generate_key();
        this.state.key = await vault.wrap(key);
        this.props.record.update({
            [this.props.field_key]: this.state.key
        })
        return key;
    }

    /**
         * Decrypt data with the master key stored in the vault
         *
         * @param {String} data
         * @returns the decrypted data
         */
    async _decrypt(data) {
        if (!supported()) return null;

        const iv = this._getIV();
        const key = await this._getMasterKey();
        return await sym_decrypt(key, data, iv);
    }

    /**
     * Encrypt data with the master key stored in the vault
     *
     * @param {String} data
     * @returns the encrypted data
     */
    async _encrypt(data) {
        if (!supported()) return null;

        const iv = this._getIV();
        const key = await this._getMasterKey();
        return await sym_encrypt(key, data, iv);
    }
}

VaultAbstract.props = {
    ...standardFieldProps,
    field_key: { type: String, optional: true },
    field_iv: { type: String, optional: true },
    acceptedFileExtensions: { type: String, optional: true },
    fileNameField: { type: String, optional: true },
};

VaultAbstract.defaultProps = {
    acceptedFileExtensions: "*",
};

VaultAbstract.extractProps = ({ field, attrs }) => {
    return {
        field_key: attrs.key || "master_key",
        field_iv: attrs.iv || "iv",
        acceptedFileExtensions: attrs.options.accepted_file_extensions || [],
        fileNameField: attrs.filename || "",
    };
};


class VaultField extends VaultAbstract {
    setup() {
        super.setup(...arguments);
        
        this.state = useState({
            decrypted: false,
            show: true,
            decrypted_value: false
        })
    }

    async _onGenerateValue(ev) {
        ev.stopPropagation();

        const password = await generate_pass();
        await this.onChange(password);
    }

    get formmatedValue() {
        return this.state.decrypted_value || "**********"
    }

}

VaultField.displayName = _lt("Vault");
VaultField.supportedTypes = ["char"];
VaultField.template = "vault.VaultField";


class VaultFile extends VaultAbstract {
    setup() {
        this.notification = useService("notification");
        this.state = useState({
            fileName: this.props.record.data[this.props.fileNameField] || "",
        });
        onWillUpdateProps((nextProps) => {
            this.state.fileName = nextProps.record.data[nextProps.fileNameField] || "";
        });
    }

    get fileName() {
        return this.state.fileName || this.props.value || "";
    }

    async update({ data, name }) {
        this.state.fileName = name || "";
        const { fileNameField, record } = this.props;
        const changes = { [this.props.name]: (data) ? await this._encrypt(data) : false };        if (fileNameField in record.fields && record.data[fileNameField] !== name) {
            changes[fileNameField] = name || false;
        }
        return this.props.record.update(changes);
    }

    async onFileDownload() {
        let file = null;
        if (!isBinarySize(this.props.value)) {
            const base64 = atob(await this._decrypt(this.props.value));
            const buffer = new ArrayBuffer(base64.length);
            const arr = new Uint8Array(buffer);
            for (let i = 0; i < base64.length; i++) arr[i] = base64.charCodeAt(i);

            file = new Blob([arr]);
        }

        await download({
            data: {
                model: this.props.record.resModel,
                id: this.props.record.resId,
                field: this.props.name,
                filename_field: this.fileName,
                filename: this.fileName || "",
                download: true,
                data: file,
            },
            url: "/web/content",
        });
    }
}

VaultFile.template = "web.BinaryField";
VaultFile.components = {
    FileUploader,
};

VaultFile.displayName = _lt("File");
VaultFile.supportedTypes = ["binary"];


class VaultExportFile extends VaultFile {
    async onFileDownload() {
        let file = null;
        if (!isBinarySize(this.props.value)) {
            const exporter = new Exporter();
            const content = JSON.stringify(
                await exporter.export(
                    await this._getMasterKey(),
                    this.fileName,
                    this.props.value
                )
            );
            const buffer = new ArrayBuffer(content.length);
            const arr = new Uint8Array(buffer);
            for (let i = 0; i < content.length; i++) arr[i] = content.charCodeAt(i);

            file = new Blob([arr]);
        }

        await download({
            data: {
                model: this.props.record.resModel,
                id: this.props.record.resId,
                field: this.props.name,
                filename_field: this.fileName,
                filename: this.fileName || "",
                download: true,
                data: file,
            },
            url: "/web/content",
        });
    }
}

class VaultInboxField extends VaultField {
    /**
         * Decrypt the data with the private key of the vault
         *
         * @private
         * @param {String} data
         * @returns the decrypted data
         */
    async _decrypt(data) {
        if (!supported()) return null;

        const iv = this.recordData[this.field_iv];
        const wrapped_key = this.recordData[this.field_key];

        if (!iv || !wrapped_key) return false;

        const key = await vault.unwrap(wrapped_key);
        return await sym_decrypt(key, data, iv);
    }
}

VaultInboxField.template = "vault.VaultInboxField";

class VaultInboxFile extends VaultFile {
    /**
         * Decrypt the data with the private key of the vault
         *
         * @private
         * @param {String} data
         * @returns the decrypted data
         */
    async _decrypt(data) {
        if (!supported()) return null;

        const iv = this.recordData[this.field_iv];
        const wrapped_key = this.recordData[this.field_key];

        if (!iv || !wrapped_key) return false;

        const key = await vault.unwrap(wrapped_key);
        return btoa(await sym_decrypt(key, data, iv));
    }
}

VaultInboxFile.template = "vault.VaultInboxFile";

registry.category("fields").add("vault", VaultField);
registry.category("fields").add("vault_file", VaultFile);
registry.category("fields").add("vault_export", VaultExportFile);
registry.category("fields").add("vault_inbox", VaultInboxField);
registry.category("fields").add("vault_inbox_file", VaultInboxFile);


export default {
    VaultAbstract: VaultAbstract,
    VaultField: VaultField,
    VaultFile: VaultFile,
    VaultExportFile: VaultExportFile,
    VaultInboxField: VaultInboxField,
    VaultInboxFile: VaultInboxFile,
}