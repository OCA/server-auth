// © 2021 Florian Kantelberg - initOS GmbH
// License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

odoo.define("vault.fields", function (require) {
    "use strict";

    const core = require("web.core");
    const basic_fields = require("web.basic_fields");
    const download = require("web.download");
    const Exporter = require("vault.export");
    const registry = require("web.field_registry");
    const utils = require("vault.utils");
    const vault = require("vault");

    const _t = core._t;
    const QWeb = core.qweb;

    const VaultAbstract = {
        supported: function () {
            return utils.supported();
        },
        /**
         * Set the value by encrypting it
         *
         * @param {String} value
         * @param {Object} options
         * @returns promise for the encryption
         */
        _setValue: function (value, options) {
            const self = this;
            const _super = this._super;

            if (utils.supported()) {
                return this._encrypt(value).then(function (data) {
                    _super.call(self, data, options);
                });
            }
        },

        /**
         * Set the value of a different field
         *
         * @param {String} field
         * @param {String} value
         */
        _setFieldValue: function (field, value) {
            const data = {};
            data[field] = value;

            this.trigger_up("field_changed", {
                dataPointID: this.dataPointID,
                changes: data,
            });
        },

        /**
         * Extract the IV or generate a new one if needed
         *
         * @returns the IV to use
         */
        _getIV: function () {
            if (!utils.supported()) return null;

            // IV already read. Reuse it
            if (this.iv) return this.iv;

            // Read the IV from the field
            this.iv = this.recordData[this.field_iv];
            if (this.iv) return this.iv;

            // Generate a new IV
            this.iv = utils.generate_iv_base64();
            this._setFieldValue(this.field_iv, this.iv);
            return this.iv;
        },

        /**
         * Extract the master key of the vault or generate a new one
         *
         * @returns the master key to use
         */
        _getMasterKey: async function () {
            if (!utils.supported()) return null;

            // Check if the master key is already extracted
            if (this.key) return await vault.unwrap(this.key);

            // Get the wrapped master key from the field
            this.key = this.recordData[this.field_key];
            if (this.key) return await vault.unwrap(this.key);

            // Generate a new master key and write it to the field
            const key = await utils.generate_key();
            this.key = await vault.wrap(key);
            this._setFieldValue(this.field_key, this.key);
            return key;
        },

        /**
         * Toggle if the value is shown or hidden, and decrypt the value if shown
         *
         * @private
         * @param {OdooEvent} ev
         */
        _onShowValue: async function (ev) {
            ev.stopPropagation();

            this.decrypted = !this.decrypted;
            if (this.decrypted) this.decrypted_value = await this._decrypt(this.value);
            else this.decrypted_value = false;

            this._render();
        },

        /**
         * Copy the decrypted value to the clipboard
         *
         * @private
         * @param {OdooEvent} ev
         */
        _onCopyValue: async function (ev) {
            ev.stopPropagation();

            const value = await this._decrypt(this.value);
            await navigator.clipboard.writeText(value);
        },

        /**
         * Send the value with an internal user
         *
         * @private
         * @param {OdooEvent} ev
         */
        _onSendValue: async function (ev) {
            ev.stopPropagation();

            const key = await utils.generate_key();
            const iv = utils.generate_iv_base64();
            const value = await this._decrypt(this.value);

            this.do_action({
                type: "ir.actions.act_window",
                title: _t("Send the secret to another user"),
                target: "new",
                res_model: "vault.send.wizard",
                views: [[false, "form"]],
                context: {
                    default_secret: await utils.sym_encrypt(key, value, iv),
                    default_iv: iv,
                    default_key: await vault.wrap(key),
                },
            });
        },

        /**
         * Save the content in an entry of a vault
         *
         * @private
         * @param {OdooEvent} ev
         */
        _onSaveValue: async function (ev) {
            ev.stopPropagation();

            const key = await utils.generate_key();
            const iv = utils.generate_iv_base64();
            const value = await this._decrypt(this.value);
            const store_model = this.store_model || "vault.field";

            this.do_action({
                type: "ir.actions.act_window",
                title: _t("Store the secret in a vault"),
                target: "new",
                res_model: "vault.store.wizard",
                views: [[false, "form"]],
                context: {
                    default_model: store_model,
                    default_secret_temporary: await utils.sym_encrypt(key, value, iv),
                    default_iv: iv,
                    default_key: await vault.wrap(key),
                },
            });
        },

        /**
         * Decrypt data with the master key stored in the vault
         *
         * @param {String} data
         * @returns the decrypted data
         */
        _decrypt: async function (data) {
            if (!utils.supported()) return null;

            const iv = this._getIV();
            const key = await this._getMasterKey();
            return await utils.sym_decrypt(key, data, iv);
        },

        /**
         * Encrypt data with the master key stored in the vault
         *
         * @param {String} data
         * @returns the encrypted data
         */
        _encrypt: async function (data) {
            if (!utils.supported()) return null;

            const iv = this._getIV();
            const key = await this._getMasterKey();
            return await utils.sym_encrypt(key, data, iv);
        },
    };

    // Basic field widget of the vault
    const VaultField = basic_fields.InputField.extend(VaultAbstract, {
        supportedFieldTypes: ["char"],
        tagName: "div",
        events: _.extend({}, basic_fields.InputField.prototype.events, {
            "click .o_vault_show": "_onShowValue",
            "click .o_vault_clipboard": "_onCopyValue",
            "click .o_vault_generate": "_onGenerateValue",
            "click .o_vault_send": "_onSendValue",
        }),
        className: "o_vault o_field_char",
        template: "FieldVault",

        /**
         * Prepare the widget by evaluating the field attributes and setting the defaults
         *
         * @override
         */
        init: function () {
            this._super.apply(this, arguments);

            this.field_key = this.attrs.key || "master_key";
            this.field_iv = this.attrs.iv || "iv";
            this.decrypted = false;
        },

        /**
         * Generate a secret
         *
         * @private
         * @param {OdooEvent} ev
         */
        _onGenerateValue: async function (ev) {
            ev.stopPropagation();

            const password = await utils.generate_pass();
            this.$el.find("input.o_vault_value")[0].value = password;
            this._setValue(password, {});
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
         * Adapt the maxlength
         *
         * @private
         * @override
         */
        _renderEdit: function () {
            if (this.field.size && this.field.size > 0)
                this.$el.attr("maxlength", this.field.size);
            return this._super.apply(this, arguments);
        },

        /**
         * Render the decrypted value or the stars
         *
         * @private
         * @param {String} value to render
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

        /**
         * Decrypt the value and show in edit mode
         *
         * @private
         * @param {JQuery} $input
         * @returns the element
         */
        _prepareInput: function ($input) {
            const self = this;
            const inputAttrs = {
                placeholder: self.attrs.placeholder || "",
                type: "text",
            };
            this.$input = $input || $("<input/>");
            this.$input.addClass("o_input");
            this.$input.attr(inputAttrs);

            if (utils.supported()) {
                this._decrypt(this.value).then(function (data) {
                    self.$input.val(self._formatValue(data));
                });
            }

            return this.$input;
        },

        /**
         * @override
         * @returns {String} the content of the input
         */
        _getValue: function () {
            return this.$("input").val();
        },
    });

    // Widget used for using encrypted files
    const VaultFile = basic_fields.FieldBinaryFile.extend(VaultAbstract, {
        className: "o_vault",

        /**
         * Prepare the widget by evaluating the field attributes and setting the defaults
         *
         * @override
         */
        init: function () {
            this._super.apply(this, arguments);

            this.field_key = this.attrs.key || "master_key";
            this.field_iv = this.attrs.iv || "iv";
        },

        /**
         * Handle on save correctly by decrypting the value before and starting the download
         *
         * @private
         * @param {OdooEvent} ev
         */
        on_save_as: async function (ev) {
            if (!this.value) {
                this.do_warn(
                    _t("Save As..."),
                    _t("The field is empty, there's nothing to save!")
                );
                ev.stopPropagation();
            } else if (this.res_id && utils.supported()) {
                ev.stopPropagation();

                const filename_fieldname = this.attrs.filename;
                const base64 = atob(await this._decrypt(this.value));
                const buffer = new ArrayBuffer(base64.length);
                const arr = new Uint8Array(buffer);
                for (let i = 0; i < base64.length; i++) arr[i] = base64.charCodeAt(i);

                const blob = new Blob([arr]);
                download(blob, this.recordData[filename_fieldname] || "");
            }
        },
    });

    // Widget used for using export
    const VaultExportFile = basic_fields.FieldBinaryFile.extend(VaultAbstract, {
        className: "o_vault",
        events: _.extend({}, basic_fields.AbstractFieldBinary.prototype.events, {
            click: function (event) {
                if (this.mode === "readonly" && this.value) this.on_save_as(event);
            },
            "click .o_input": function () {
                this.$(".o_input_file").click();
            },
        }),

        /**
         * Prepare the widget by evaluating the field attributes and setting the defaults
         *
         * @override
         */
        init: function () {
            this._super.apply(this, arguments);

            this.field_key = this.attrs.key || "master_key";
        },

        /**
         * Render the widget always like the normal widget in readonly mode
         *
         * @private
         * @override
         */
        _render: function () {
            if (this.value) {
                this.$el.empty().append($("<span/>").addClass("fa fa-download"));
                this.$el.css("cursor", "pointer");

                if (this.filename_value) this.$el.append(" " + this.filename_value);
            } else this.$el.css("cursor", "not-allowed");
        },

        /**
         * Handle on save correctly by decrypting the value before and starting the download
         *
         * @private
         * @param {OdooEvent} ev
         */
        on_save_as: async function (ev) {
            if (this.value && utils.supported()) {
                ev.stopPropagation();

                const exporter = new Exporter();
                const content = JSON.stringify(
                    await exporter.export(
                        await this._getMasterKey(),
                        this.filename_value,
                        this.value
                    )
                );
                const buffer = new ArrayBuffer(content.length);
                const arr = new Uint8Array(buffer);
                for (let i = 0; i < content.length; i++) arr[i] = content.charCodeAt(i);

                const blob = new Blob([arr]);
                download(blob, this.filename_value || "");
            } else {
                this.do_warn(
                    _t("Save As..."),
                    _t("The field is empty, there's nothing to save!")
                );
                ev.stopPropagation();
            }
        },
    });

    const VaultInboxField = VaultField.extend({
        store_model: "vault.field",
        events: _.extend({}, VaultField.prototype.events, {
            "click .o_vault_show": "_onShowValue",
            "click .o_vault_clipboard": "_onCopyValue",
            "click .o_vault_save": "_onSaveValue",
        }),
        template: "FieldVaultInbox",

        /**
         * Prepare the widget by evaluating the field attributes and setting the defaults
         *
         * @override
         */
        init: function () {
            this._super.apply(this, arguments);

            this.field_iv = this.attrs.iv || "iv";
            this.field_key = this.attrs.key || "key";
            this.decrypted = false;
        },

        /**
         * Decrypt the data with the private key of the vault
         *
         * @private
         * @param {String} data
         * @returns the decrypted data
         */
        _decrypt: async function (data) {
            if (!utils.supported()) return null;

            const iv = this.recordData[this.field_iv];
            const wrapped_key = this.recordData[this.field_key];

            if (!iv || !wrapped_key) return false;

            const key = await vault.unwrap(wrapped_key);
            return await utils.sym_decrypt(key, data, iv);
        },

        /**
         * Render the decrypted value or the stars
         *
         * @private
         */
        _renderEdit: function () {
            this._renderReadonly();
        },
    });

    // Widget used to view shared incoming secrets encrypted with public keys
    const VaultInboxFile = VaultFile.extend({
        store_model: "vault.file",
        template: "FileVaultInbox",
        events: _.extend({}, VaultFile.prototype.events, {
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
            this.decrypted = false;
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
         * Decrypt the data with the private key of the vault
         *
         * @private
         * @param {String} data
         * @returns the decrypted data
         */
        _decrypt: async function (data) {
            if (!utils.supported()) return null;

            const iv = this.recordData[this.field_iv];
            const wrapped_key = this.recordData[this.field_key];

            if (!iv || !wrapped_key) return false;

            const key = await vault.unwrap(wrapped_key);
            return btoa(await utils.sym_decrypt(key, data, iv));
        },
    });

    registry.add("vault", VaultField);
    registry.add("vault_file", VaultFile);
    registry.add("vault_export", VaultExportFile);
    registry.add("vault_inbox", VaultInboxField);
    registry.add("vault_inbox_file", VaultInboxFile);

    return {
        VaultAbstract: VaultAbstract,
        VaultField: VaultField,
        VaultFile: VaultFile,
        VaultExportFile: VaultExportFile,
        VaultInboxFile: VaultInboxFile,
        VaultInboxField: VaultInboxField,
    };
});
