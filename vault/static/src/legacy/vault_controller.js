// © 2021 Florian Kantelberg - initOS GmbH
// License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

odoo.define("vault.controller", function (require) {
    "use strict";

    var core = require("web.core");
    var Dialog = require("web.Dialog");
    var FormController = require("web.FormController");
    var framework = require("web.framework");
    var Importer = require("vault.import");
    var utils = require("vault.utils");
    var vault = require("vault");

    var _t = core._t;

    FormController.include({
        events: _.extend({}, FormController.prototype.events, {
            "click [name='vault_reencrypt']": "_clickReencryptVault",
            "click [name='vault_verify']": "_clickVerifyVault",
        }),

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
            // Get the current private key
            const private_key = await vault.get_private_key();

            // Generate new keys
            await vault.generate_keys();

            const public_key = await vault.get_public_key();

            // Re-encrypt the master keys
            const master_keys = await this._rpc({route: "/vault/rights/get"});
            let result = {};
            for (const uuid in master_keys) {
                result[uuid] = await utils.wrap(
                    await utils.unwrap(master_keys[uuid], private_key),
                    public_key
                );
            }

            await this._rpc({route: "/vault/rights/store", params: {keys: result}});

            // Re-encrypt the inboxes to not loose it
            const inbox_keys = await this._rpc({route: "/vault/inbox/get"});
            result = {};
            for (const uuid in inbox_keys) {
                result[uuid] = await utils.wrap(
                    await utils.unwrap(inbox_keys[uuid], private_key),
                    public_key
                );
            }

            await this._rpc({route: "/vault/inbox/store", params: {keys: result}});

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

        _clickReencryptVault: async function () {
            await this._reencryptVault(false, true);
        },

        _clickVerifyVault: async function () {
            await this._reencryptVault(true, false);
        },

        /**
         * Handle the deletion of a vault.right field in the vault view properly by
         * generating a new master key and re-encrypting everything in the vault to
         * deny any future access to the vault.
         *
         * @private
         * @param {Boolean} verify
         * @param {Boolean} force
         */
        _reencryptVault: async function (verify = false, force = false) {
            const record = this.model.get(this.handle);

            await vault._ensure_keys();

            const self = this;
            const master_key = await utils.generate_key();
            const current_key = await vault.unwrap(record.data.master_key);

            // This stores the additional changes made to rights, fields, and files
            const changes = [];
            const problems = [];

            async function reencrypt(model, type) {
                // Load the entire data from the database
                const handle = await self.model.load({
                    context: {vault_reencrypt: true},
                    domain: [["vault_id", "=", record.res_id]],
                    fields: ["iv", "value", "name", "entry_name"],
                    modelName: model,
                    limit: 0,
                    type: "list",
                });

                const records = await self.model.get(handle, {raw: true});
                for (const rec of records.data) {
                    if (!rec.data) continue;

                    const d = rec.data;
                    const val = await utils.sym_decrypt(current_key, d.value, d.iv);
                    if (val === null) {
                        problems.push(
                            _.str.sprintf(
                                _t("%s '%s' of entry '%s'"),
                                type,
                                d.name,
                                d.entry_name
                            )
                        );
                        continue;
                    }

                    const iv = utils.generate_iv_base64();
                    const encrypted = await utils.sym_encrypt(master_key, val, iv);

                    changes.push({
                        id: rec.res_id,
                        model: model,
                        value: encrypted,
                        iv: iv,
                    });
                }
            }

            framework.blockUI();
            try {
                // Update the rights. Load without limit
                const right_handle = await this.model.load({
                    domain: [["vault_id", "=", record.res_id]],
                    fields: ["key"],
                    modelName: "vault.right",
                    limit: 0,
                    type: "list",
                });

                const rights = await this.model.get(right_handle, {raw: true});
                for (const right of rights.data) {
                    const key = await vault.wrap_with(
                        master_key,
                        right.data.public_key
                    );

                    changes.push({
                        id: right.res_id,
                        model: "vault.right",
                        key: key,
                    });
                }

                // Re-encrypt vault.field and vault.file
                await reencrypt("vault.field", "Field");
                await reencrypt("vault.file", "File");

                if (problems && !force) {
                    framework.unblockUI();

                    Dialog.alert(self, "", {
                        title: _t("The following entries are broken:"),
                        $content: $("<div/>").html(problems.join("<br>\n")),
                    });
                }

                if (!verify) {
                    await this._rpc({
                        route: "/vault/replace",
                        params: {data: changes},
                    });
                    this.reload();
                }
            } finally {
                framework.unblockUI();
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
