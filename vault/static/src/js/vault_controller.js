// © 2021 Florian Kantelberg - initOS GmbH
// License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

odoo.define("vault.controller", function (require) {
    "use strict";

    var core = require("web.core");
    var Dialog = require("web.Dialog");
    var FormController = require("web.FormController");
    var Importer = require("vault.import");
    var utils = require("vault.utils");
    var vault = require("vault");

    var _t = core._t;

    FormController.include({
        /**
         * Re-encrypt the key if the user is getting selected
         *
         * @private
         * @param {Object} record
         * @param {Object} changes
         * @param {Object} options
         */
        _applyChangesSendWizard: async function (record, changes, options) {
            if (!changes.user_id || !record.data.public) return;

            const key = await vault.unwrap(record.data.key);
            await this._applyChanges(
                record.id,
                {key_user: await vault.wrap_with(key, record.data.public)},
                options
            );
        },

        /**
         * Re-encrypt the key if the entry is getting selected
         *
         * @private
         * @param {Object} record
         * @param {Object} changes
         * @param {Object} options
         */
        _applyChangesStoreWizard: async function (record, changes, options) {
            if (
                !changes.entry_id ||
                !record.data.master_key ||
                !record.data.iv ||
                !record.data.secret_temporary
            )
                return;

            const key = await vault.unwrap(record.data.key);
            const secret = await utils.sym_decrypt(
                key,
                record.data.secret_temporary,
                record.data.iv
            );
            const master_key = await vault.unwrap(record.data.master_key);

            await this._applyChanges(
                record.id,
                {secret: await utils.sym_encrypt(master_key, secret, record.data.iv)},
                options
            );
        },

        /**
         * Generate a new key pair for the current user
         *
         * @private
         */
        _newVaultKeyPair: async function () {
            const master_keys = await this._rpc({route: "/vault/rights/get"});

            // Get the current private key
            const private_key = await vault.get_private_key();

            // Generate new keys
            await vault.generate_keys();

            const public_key = await vault.get_public_key();

            // Re-encrypt the master keys
            const result = {};
            for (const uuid in master_keys) {
                result[uuid] = await utils.wrap(
                    await utils.unwrap(master_keys[uuid], private_key),
                    public_key
                );
            }

            await this._rpc({route: "/vault/rights/store", params: {keys: result}});

            await this.reload();
        },

        /**
         * Generate a new key pair and re-encrypt the master keys of the vaults
         *
         * @private
         * @param {OdooEvent} ev
         */
        _onGenerateKeys: async function (ev) {
            ev.stopPropagation();
            if (!utils.supported()) return;

            var self = this;

            Dialog.confirm(
                self,
                _t("Do you really want to create a new key pair and set it active?"),
                {
                    confirm_callback: function () {
                        return self._newVaultKeyPair();
                    },
                }
            );
        },

        /**
         * Hook into the button to generate new key pairs
         *
         * @private
         */
        renderButtons: function () {
            this._super.apply(this, arguments);

            if (this.modelName !== "res.users") return;

            if (this.$buttons)
                this.$buttons.on(
                    "click",
                    "[name='action_generate_key']",
                    this._onGenerateKeys.bind(this)
                );
        },

        /**
         * Handle changes of vault.right field in the vault view properly by
         * sharing the master key with the user
         *
         * @private
         * @param {Object} record
         * @param {Object} changes
         * @param {Object} options
         */
        _changedVaultRightUser: async function (record, changes, options) {
            if (!changes.data.user_id) return;

            const params = {user_id: changes.data.user_id.id};
            const user = await this._rpc({route: "/vault/public", params: params});

            if (!user || !user.public_key)
                throw new TypeError("User has no public key");

            for (const right of record.data.right_ids.data) {
                if (right.id === changes.id) {
                    const key = await vault.share(
                        record.data.master_key,
                        user.public_key
                    );
                    await this._applyChanges(
                        record.id,
                        {
                            right_ids: {
                                operation: "UPDATE",
                                id: right.id,
                                data: {key: key},
                            },
                        },
                        options
                    );
                }
            }
        },

        /**
         * Handle the deletion of a vault.right field in the vault view properly by
         * generating a new master key and re-encrypting everything in the vault to
         * deny any future access to the vault.
         *
         * @private
         * @param {Object} record
         * @param {Object} changes
         * @param {Object} options
         */
        _deleteVaultRight: async function (record, changes, options) {
            const master_key = await utils.generate_key();
            const current_key = await vault.unwrap(record.data.master_key);

            // Update the rights
            for (const right of record.data.right_ids.data) {
                if (changes.ids.indexOf(right.id) < 0) {
                    const key = await vault.wrap_with(
                        master_key,
                        right.data.public_key
                    );

                    await this._applyChanges(
                        record.id,
                        {
                            right_ids: {
                                operation: "UPDATE",
                                id: right.id,
                                data: {key: key},
                            },
                        },
                        options
                    );
                }
            }

            // Re-encrypt the fields
            for (const field of record.data.field_ids.data) {
                const val = await utils.sym_decrypt(
                    current_key,
                    field.data.value,
                    field.data.iv
                );
                const iv = utils.generate_iv_base64();
                const encrypted = await utils.sym_encrypt(master_key, val, iv);

                await this._applyChanges(
                    record.id,
                    {
                        field_ids: {
                            operation: "UPDATE",
                            id: field.id,
                            data: {value: encrypted, iv: iv},
                        },
                    },
                    options
                );
            }

            // Re-encrypt the files
            for (const file of record.data.file_ids.data) {
                const val = await utils.sym_decrypt(
                    current_key,
                    file.data.content,
                    file.data.iv
                );
                const iv = utils.generate_iv_base64();
                const encrypted = await utils.sym_encrypt(master_key, val, iv);

                await this._applyChanges(
                    record.id,
                    {
                        file_ids: {
                            operation: "UPDATE",
                            id: file.id,
                            data: {content: encrypted, iv: iv},
                        },
                    },
                    options
                );
            }
        },

        /**
         * Handle changes to the vault properly and call the specific function for the cases above.
         * Generate a master key if there is not one yet
         *
         * @private
         * @param {Object} record
         * @param {Object} changes
         * @param {Object} options
         */
        _applyChangesVault: async function (record, changes, options) {
            if (!record.data.master_key && !changes.master_key) {
                const master_key = await vault.wrap(await utils.generate_key());
                await this._applyChanges(record.id, {master_key: master_key}, options);
            }

            if (changes.right_ids && changes.right_ids.operation === "UPDATE")
                await this._changedVaultRightUser(record, changes.right_ids, options);

            if (changes.right_ids && changes.right_ids.operation === "DELETE") {
                const self = this;

                Dialog.confirm(
                    self,
                    _t(
                        "This will re-encrypt everything in the vault. Do you want to proceed?"
                    ),
                    {
                        confirm_callback: async function () {
                            await self._deleteVaultRight(
                                record,
                                changes.right_ids,
                                options
                            );
                        },
                    }
                );
            }
        },

        /**
         * Call the right importer in the import wizard onchange of the content field
         *
         * @private
         * @param {Object} record
         * @param {Object} changes
         * @param {Object} options
         */
        _applyChangesImportWizard: async function (record, changes, options) {
            if (!changes.content) return;

            // Try to import the file on the fly and store the compatible JSON in the
            // crypted_content field for the python backend
            const importer = new Importer();
            const data = await importer.import(
                await vault.unwrap(record.data.master_key),
                record.data.name,
                atob(changes.content)
            );

            if (data)
                await this._applyChanges(
                    record.id,
                    {crypted_content: JSON.stringify(data)},
                    options
                );
        },

        /**
         * Check the model of the form and call the above functions for the right case
         *
         * @private
         * @param {String} dataPointID
         * @param {Object} changes
         * @param {Object} options
         */
        _applyChanges: async function (dataPointID, changes, options) {
            const result = await this._super.apply(this, arguments);

            if (!utils.supported()) return result;

            const record = this.model.get(dataPointID);
            if (record.model === "vault")
                await this._applyChangesVault(record, changes, options);
            else if (record.model === "vault.send.wizard")
                await this._applyChangesSendWizard(record, changes, options);
            else if (record.model === "vault.store.wizard")
                await this._applyChangesStoreWizard(record, changes, options);
            else if (record.model === "vault.import.wizard")
                await this._applyChangesImportWizard(record, changes, options);

            return result;
        },
    });
});
