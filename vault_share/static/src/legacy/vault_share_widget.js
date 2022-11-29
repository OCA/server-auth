// © 2021 Florian Kantelberg - initOS GmbH
// License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

odoo.define("vault.share.widget", function (require) {
    "use strict";

    const basic_fields = require("web.basic_fields");
    const core = require("web.core");
    const registry = require("web.field_registry");
    const sh_utils = require("vault.share.utils");
    const utils = require("vault.utils");
    const vault = require("vault");
    const vault_fields = require("vault.fields");

    const QWeb = core.qweb;

    // Widget used to view the encrypted pin
    const VaultPinField = basic_fields.InputField.extend(vault_fields.VaultAbstract, {
        supportedFieldTypes: ["char"],
        events: _.extend({}, basic_fields.InputField.prototype.events, {
            "click .o_vault_show": "_onShowValue",
            "click .o_vault_clipboard": "_onCopyValue",
        }),
        template: "FieldPinVault",

        /**
         * Prepare the widget by evaluating the field attributes and setting the defaults
         *
         * @override
         */
        init: function () {
            this._super.apply(this, arguments);

            this.pin_size = this.attrs.pin_size || sh_utils.PinSize;
        },

        /**
         * Decrypt the value using the private key of the vault and slice it to
         * the actual pin size because there is a salt following
         *
         * @private
         * @param {String} data
         * @returns the decrypted data
         */
        _decrypt: async function (data) {
            if (!data) return data;

            const private_key = await vault.get_private_key();
            const plain = await utils.asym_decrypt(private_key, data);
            return plain.slice(0, this.pin_size);
        },

        /**
         * Render the decrypted value or the stars
         *
         * @private
         */
        _renderReadonly: function () {
            this._renderValue(this.decrypted_value || "********");
        },

        /**
         * Render the decrypted value or the stars
         *
         * @private
         */
        _renderEdit: function () {
            this._renderValue(this.decrypted_value || "********");
        },

        /**
         * Render the field using the template
         *
         * @private
         * @param {String} value
         */
        _renderValue: function (value) {
            const self = this;
            this.$el.html(
                QWeb.render(this.template, {
                    widget: self,
                    value: value,
                    show: !this.decrypted,
                })
            );
        },
    });

    // Widget used to create shared outgoing secrets encrypted with a pin
    const VaultShareField = vault_fields.VaultField.extend({
        events: _.extend({}, vault_fields.VaultField.prototype.events, {
            "click .o_vault_save": "_onSaveValue",
        }),
        template: "FieldVaultShare",

        /**
         * Prepare the widget by evaluating the field attributes and setting the defaults
         *
         * @override
         */
        init: function () {
            this._super.apply(this, arguments);

            this.pin_size = this.attrs.pin_size || sh_utils.PinSize;
            this.field_salt = this.attrs.salt || "salt";
            this.field_pin = this.attrs.pin || "pin";
        },

        /**
         * Encrypt the pin with a random salt to make it hard to guess him by
         * encrypting every possilbilty with the public key. Store the pin in the
         * proper field
         *
         * @private
         */
        _storePin: async function () {
            const salt = utils.generate_iv_base64();
            const crypted_pin = await utils.asym_encrypt(
                await vault.get_public_key(),
                this.pin + salt
            );
            this._setFieldValue(this.field_pin, crypted_pin);
        },

        /**
         * Returns the pin from the class, record data, or generate a new pin if
         * none s currently available
         *
         * @private
         * @returns the pin
         */
        _getPin: async function () {
            if (this.pin) return this.pin;

            this.pin = this.recordData[this.field_pin];
            if (this.pin) {
                // Decrypt the pin and slice him to the configured pin size
                const private_key = await vault.get_private_key();
                const plain = await utils.asym_decrypt(private_key, this.pin);
                this.pin = plain.slice(0, this.pin_size);
                return this.pin;
            }

            // Generate a new pin and store it
            this.pin = sh_utils.generate_pin(this.pin_size);
            await this._storePin();
            return this.pin;
        },

        /**
         * Returns the salt from the class, record data, or generate a new salt if
         * none is currently available
         *
         * @private
         * @returns the salt
         */
        _getSalt: function () {
            if (this.salt) return this.salt;

            this.salt = this.recordData[this.field_salt];
            if (this.salt) return this.salt;

            // Generate a new salt and store him
            this.salt = utils.toBase64(utils.generate_bytes(utils.SaltLength).buffer);
            this._setFieldValue(this.field_salt, this.salt);
            return this.salt;
        },

        /**
         * Decrypt the encrypted data using the pin, IV and salt
         *
         * @private
         * @param {String} crypted
         */
        _decrypt: async function (crypted) {
            if (crypted === false) return false;

            if (!utils.supported()) return null;

            const iv = this._getIV();
            const pin = await this._getPin();
            const salt = utils.fromBase64(this._getSalt());

            const key = await utils.derive_key(pin, salt, 4000);
            return await utils.sym_decrypt(key, crypted, iv);
        },

        /**
         * Encrypt the data using the pin, IV and salt
         *
         * @private
         * @param {String} data
         */
        _encrypt: async function (data) {
            if (!utils.supported()) return null;

            const iv = this._getIV();
            const pin = await this._getPin();
            const salt = utils.fromBase64(this._getSalt());

            const key = await utils.derive_key(pin, salt, 4000);
            return await utils.sym_encrypt(key, data, iv);
        },

        /**
         * Resets the content to the formated value in readonly mode.
         *
         * @override
         * @private
         */
        _renderReadonly: function () {
            const self = this;
            this.$el.html(
                QWeb.render(this.template, {
                    widget: self,
                    value: this.decrypted_value || "********",
                    show: !this.decrypted,
                })
            );
        },

        /**
         * @override
         * @returns {String} the content of the input
         */
        _getValue: function () {
            return this.$input.val();
        },
    });

    // Widget used to view shared incoming secrets encrypted with public keys
    const VaultShareFile = vault_fields.VaultFile.extend({
        store_model: "vault.file",
        template: "FileVaultShare",
        events: _.extend({}, vault_fields.VaultFile.prototype.events, {
            "click .o_vault_save": "_onSaveValue",
        }),

        /**
         * Prepare the widget by evaluating the field attributes and setting the defaults
         *
         * @override
         */
        init: function () {
            this._super.apply(this, arguments);

            this.field_key = this.attrs.key || "key";
            this.pin_size = this.attrs.pin_size || sh_utils.PinSize;
            this.field_salt = this.attrs.salt || "salt";
            this.field_pin = this.attrs.pin || "pin";
        },

        /**
         * Encrypt the pin with a random salt to make it hard to guess him by
         * encrypting every possilbilty with the public key. Store the pin in the
         * proper field
         *
         * @private
         */
        _storePin: async function () {
            const salt = utils.generate_iv_base64();
            const crypted_pin = await utils.asym_encrypt(
                await vault.get_public_key(),
                this.pin + salt
            );
            this._setFieldValue(this.field_pin, crypted_pin);
        },

        /**
         * Returns the pin from the class, record data, or generate a new pin if
         * none s currently available
         *
         * @private
         * @returns the pin
         */
        _getPin: async function () {
            if (this.pin) return this.pin;

            this.pin = this.recordData[this.field_pin];
            if (this.pin) {
                // Decrypt the pin and slice him to the configured pin size
                const private_key = await vault.get_private_key();
                const plain = await utils.asym_decrypt(private_key, this.pin);
                this.pin = plain.slice(0, this.pin_size);
                return this.pin;
            }

            // Generate a new pin and store it
            this.pin = sh_utils.generate_pin(this.pin_size);
            await this._storePin();
            return this.pin;
        },

        /**
         * Returns the salt from the class, record data, or generate a new salt if
         * none is currently available
         *
         * @private
         * @returns the salt
         */
        _getSalt: function () {
            if (this.salt) return this.salt;

            this.salt = this.recordData[this.field_salt];
            if (this.salt) return this.salt;

            // Generate a new salt and store him
            this.salt = utils.toBase64(utils.generate_bytes(utils.SaltLength).buffer);
            this._setFieldValue(this.field_salt, this.salt);
            return this.salt;
        },

        _renderReadonly: function () {
            this.do_toggle(Boolean(this.value));
            if (this.value) {
                this.$el.html(
                    QWeb.render(this.template, {
                        widget: this,
                        filename: this.filename_value,
                    })
                );

                const $el = this.$(".link");
                if (this.recordData.id) $el.css("cursor", "pointer");
                else $el.css("cursor", "not-allowed");
            }
        },

        /**
         * Decrypt the encrypted data using the pin, IV and salt
         *
         * @private
         * @param {String} crypted
         */
        _decrypt: async function (crypted) {
            if (!utils.supported()) return null;

            const iv = this._getIV();
            const pin = await this._getPin();
            const salt = utils.fromBase64(this._getSalt());

            const key = await utils.derive_key(pin, salt, 4000);
            return await utils.sym_decrypt(key, crypted, iv);
        },

        /**
         * Encrypt the data using the pin, IV and salt
         *
         * @private
         * @param {String} data
         */
        _encrypt: async function (data) {
            if (!utils.supported()) return null;

            const iv = this._getIV();
            const pin = await this._getPin();
            const salt = utils.fromBase64(this._getSalt());

            const key = await utils.derive_key(pin, salt, 4000);
            return await utils.sym_encrypt(key, data, iv);
        },
    });

    registry.add("vault_pin", VaultPinField);
    registry.add("vault_share", VaultShareField);
    registry.add("vault_share_file", VaultShareFile);
});
