/** @odoo-module alias=vault.mixin **/
// © 2021-2024 Florian Kantelberg - initOS GmbH
// License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import {_lt} from "@web/core/l10n/translation";
import {standardFieldProps} from "@web/views/fields/standard_field_props";
import utils from "vault.utils";
import vault from "vault";

export default (x) => {
    class Extended extends x {
        supported() {
            return utils.supported();
        }

        // Control the visibility of the buttons
        get showButton() {
            return this.props.value;
        }
        get copyButton() {
            return this.props.value;
        }
        get sendButton() {
            return this.props.value;
        }
        get saveButton() {
            return this.props.value;
        }
        get generateButton() {
            return true;
        }
        get isNew() {
            return Boolean(this.model.record.isNew);
        }

        /**
         * Set the value by encrypting it
         *
         * @param {String} value
         * @param {Object} options
         */
        async storeValue(value, options) {
            if (!utils.supported()) return;

            const encrypted = await this._encrypt(value);
            await this.props.update(encrypted, options);
        }

        /**
         * Send the value to an inbox
         *
         * @param {String} value_field
         * @param {String} value_file
         * @param {String} filename
         */
        async sendValue(value_field = "", value_file = "", filename = "") {
            if (!utils.supported()) return;

            if (!value_field && !value_file) return;

            let enc_field = false,
                enc_file = false;

            // Prepare the key and iv for the reencryption
            const key = await utils.generate_key();
            const iv = utils.generate_iv_base64();

            // Reencrypt the field
            if (value_field) {
                const decrypted = await this._decrypt(value_field);
                enc_field = await utils.sym_encrypt(key, decrypted, iv);
            }

            // Reencrypt the file
            if (value_file) {
                const decrypted = await this._decrypt(value_file);
                enc_file = await utils.sym_encrypt(key, decrypted, iv);
            }

            // Call the wizard to handle the user selection and storage
            this.action.doAction({
                type: "ir.actions.act_window",
                title: _lt("Send the secret to another user"),
                target: "new",
                res_model: "vault.send.wizard",
                views: [[false, "form"]],
                context: {
                    default_secret: enc_field,
                    default_secret_file: enc_file,
                    default_filename: filename || false,
                    default_iv: iv,
                    default_key: await vault.wrap(key),
                },
            });
        }

        /**
         * Set the value of a different field
         *
         * @param {String} field
         * @param {String} value
         */
        async _setFieldValue(field, value) {
            this.props.record.update({[field]: value});
        }

        /**
         * Extract the IV or generate a new one if needed
         *
         * @returns the IV to use
         */
        async _getIV() {
            if (!utils.supported()) return null;

            // Read the IV from the field
            let iv = this.props.record.data[this.props.fieldIV];
            if (iv) return iv;

            // Generate a new IV
            iv = utils.generate_iv_base64();
            await this._setFieldValue(this.props.fieldIV, iv);
            return iv;
        }

        /**
         * Extract the master key of the vault or generate a new one
         *
         * @returns the master key to use
         */
        async _getMasterKey() {
            if (!utils.supported()) return null;

            // Check if the master key is already extracted
            if (this.key) return await vault.unwrap(this.key);

            // Get the wrapped master key from the field
            this.key = this.props.record.data[this.props.fieldKey];
            if (this.key) return await vault.unwrap(this.key);

            // Generate a new master key and write it to the field
            const key = await utils.generate_key();
            this.key = await vault.wrap(key);
            await this._setFieldValue(this.props.fieldKey, this.key);
            return key;
        }

        /**
         * Decrypt data with the master key stored in the vault
         *
         * @param {String} data
         * @returns the decrypted data
         */
        async _decrypt(data) {
            if (!utils.supported()) return null;

            const iv = await this._getIV();
            const key = await this._getMasterKey();
            return await utils.sym_decrypt(key, data, iv);
        }

        /**
         * Encrypt data with the master key stored in the vault
         *
         * @param {String} data
         * @returns the encrypted data
         */
        async _encrypt(data) {
            if (!utils.supported()) return null;

            const iv = await this._getIV();
            const key = await this._getMasterKey();
            return await utils.sym_encrypt(key, data, iv);
        }
    }

    Extended.defaultProps = {
        ...x.defaultProps,
        fieldIV: "iv",
        fieldKey: "master_key",
    };
    Extended.props = {
        ...standardFieldProps,
        ...x.props,
        fieldKey: {type: String, optional: true},
        fieldIV: {type: String, optional: true},
    };
    Extended.extractProps = ({attrs, field}) => {
        const extract_props = x.extractProps || (() => ({}));
        return {
            ...extract_props({attrs, field}),
            fieldKey: attrs.key,
            fieldIV: attrs.iv,
        };
    };

    return Extended;
};
