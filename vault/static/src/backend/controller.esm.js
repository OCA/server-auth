/** @odoo-module alias=vault.controller **/
// © 2021-2024 Florian Kantelberg - initOS GmbH
// License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import {AlertDialog} from "@web/core/confirmation_dialog/confirmation_dialog";
import Dialog from "web.Dialog";
import {FormController} from "@web/views/form/form_controller";
import Importer from "vault.import";
import {ListController} from "@web/views/list/list_controller";
import {_lt} from "@web/core/l10n/translation";
import framework from "web.framework";
import {patch} from "@web/core/utils/patch";
import {useService} from "@web/core/utils/hooks";
import utils from "vault.utils";
import vault from "vault";

patch(FormController.prototype, "vault", {
    /**
     * Re-encrypt the key if the user is getting selected
     *
     * @private
     */
    async _vaultSendWizard() {
        const record = this.model.root;
        if (record.resModel !== "vault.send.wizard") return;

        if (!record.data.user_id || !record.data.public) return;

        const key = await vault.unwrap(record.data.key);
        await record.update({key_user: await vault.wrap_with(key, record.data.public)});
    },

    /**
     * Re-encrypt the key if the entry is getting selected
     *
     * @private
     * @param {Object} record
     * @param {Object} changes
     * @param {Object} options
     */
    async _vaultStoreWizard() {
        const record = this.model.root;
        if (
            !record.data.entry_id ||
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

        await record.update({
            secret: await utils.sym_encrypt(master_key, secret, record.data.iv),
        });
    },

    /**
     * Generate a new key pair for the current user
     *
     * @private
     */
    async _newVaultKeyPair() {
        // Get the current private key
        const private_key = await vault.get_private_key();

        // Generate new keys
        await vault.generate_keys();

        const public_key = await vault.get_public_key();

        // Re-encrypt the master keys
        const master_keys = await this.rpc("/vault/rights/get");
        let result = {};
        for (const uuid in master_keys) {
            result[uuid] = await utils.wrap(
                await utils.unwrap(master_keys[uuid], private_key),
                public_key
            );
        }

        await this.rpc("/vault/rights/store", {keys: result});

        // Re-encrypt the inboxes to not loose it
        const inbox_keys = await this.rpc("/vault/inbox/get");
        result = {};
        for (const uuid in inbox_keys) {
            result[uuid] = await utils.wrap(
                await utils.unwrap(inbox_keys[uuid], private_key),
                public_key
            );
        }

        await this.rpc("/vault/inbox/store", {keys: result});
    },

    /**
     * Generate a new key pair and re-encrypt the master keys of the vaults
     *
     * @private
     */
    async _vaultRegenerateKey() {
        if (!utils.supported()) return;

        var self = this;

        Dialog.confirm(
            self,
            _lt("Do you really want to create a new key pair and set it active?"),
            {
                confirm_callback: function () {
                    return self._newVaultKeyPair();
                },
            }
        );
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
    async _reencryptVault(verify = false, force = false) {
        const record = this.model.root;

        await vault._ensure_keys();

        const self = this;
        const master_key = await utils.generate_key();
        const current_key = await vault.unwrap(record.data.master_key);

        // This stores the additional changes made to rights, fields, and files
        const changes = [];
        const problems = [];

        async function reencrypt(model, type) {
            // Load the entire data from the database
            const records = await self.model.orm.searchRead(
                model,
                [["vault_id", "=", record.resId]],
                ["iv", "value", "name", "entry_name"],
                {
                    context: {vault_reencrypt: true},
                    limit: 0,
                }
            );

            for (const rec of records) {
                const val = await utils.sym_decrypt(current_key, rec.value, rec.iv);
                if (val === null) {
                    problems.push(
                        _.str.sprintf(
                            _lt("%s '%s' of entry '%s'"),
                            type,
                            rec.name,
                            rec.entry_name
                        )
                    );
                    continue;
                }

                const iv = utils.generate_iv_base64();
                const encrypted = await utils.sym_encrypt(master_key, val, iv);

                changes.push({
                    id: rec.id,
                    model: model,
                    value: encrypted,
                    iv: iv,
                });
            }
        }

        framework.blockUI();
        try {
            // Update the rights. Load without limit
            const rights = await self.model.orm.searchRead(
                "vault.right",
                [["vault_id", "=", record.resId]],
                ["public_key"],
                {limit: 0}
            );

            for (const right of rights) {
                const key = await vault.wrap_with(master_key, right.public_key);

                changes.push({
                    id: right.id,
                    model: "vault.right",
                    key: key,
                });
            }

            // Re-encrypt vault.field and vault.file
            await reencrypt("vault.field", "Field");
            await reencrypt("vault.file", "File");

            if (problems.length && !force) {
                framework.unblockUI();

                Dialog.alert(self, "", {
                    title: _lt("The following entries are broken:"),
                    $content: $("<div/>").html(problems.join("<br>\n")),
                });
            }

            if (!verify) {
                await this.rpc("/vault/replace", {data: changes});
                await this.model.root.load();
            }
        } finally {
            framework.unblockUI();
        }
    },

    /**
     * Call the right importer in the import wizard onchange of the content field
     *
     * @private
     */
    async _vaultImportWizard() {
        const record = this.model.root;
        if (record.resModel !== "vault.import.wizard") return;

        // Try to import the file on the fly and store the compatible JSON in the
        // crypted_content field for the python backend
        const importer = new Importer();
        const data = await importer.import(
            await vault.unwrap(record.data.master_key),
            record.data.name,
            atob(record.data.content)
        );

        if (data) await record.update({crypted_content: JSON.stringify(data)});
    },

    /**
     * Ensure that a vault.right as the shared master_key set
     *
     * @private
     * @param {Object} root
     * @param {Object} right
     */
    async _vaultEnsureRightKey(root, right) {
        if (!root.data.master_key || right.data.key) return;

        const params = {user_id: right.data.user_id[0]};
        const user = await this.rpc("/vault/public", params);

        if (!user || !user.public_key) throw new TypeError("User has no public key");

        await right.update({
            key: await vault.share(root.data.master_key, user.public_key),
        });
    },

    /**
     * Ensures that the master_key of the vault and right lines are set
     *
     * @private
     */
    async _vaultEnsureKeys() {
        const root = this.model.root;
        if (root.resModel !== "vault") return;

        if (!root.data.master_key)
            await root.update({
                master_key: await vault.wrap(await utils.generate_key()),
            });

        if (root.data.right_ids)
            for (const right of root.data.right_ids.records)
                await this._vaultEnsureRightKey(root, right);
    },

    /**
     * Check the model of the form and call the above functions for the right case
     *
     * @private
     * @param {Object} button
     */
    async _vaultAction(button) {
        if (!utils.supported()) {
            await this.dialogService.add(AlertDialog, {
                title: _lt("Vault is not supported"),
                body: _lt(
                    "A secure browser context is required. Please switch to " +
                        "https or contact your administrator"
                ),
            });
            return false;
        }

        const root = this.model.root;
        switch (root.resModel) {
            case "res.users":
                if (button && button.name === "vault_generate_key") {
                    await this._vaultRegenerateKey();
                    return false;
                }
                break;
            case "vault":
                if (button && button.name === "vault_reencrypt") {
                    await this._reencryptVault(false, true);
                    return false;
                } else if (button && button.name === "vault_verify") {
                    await this._reencryptVault(true, false);
                    return false;
                }

                await this._vaultEnsureKeys();
                break;

            case "vault.send.wizard":
                await this._vaultSendWizard();
                break;

            case "vault.store.wizard":
                await this._vaultStoreWizard();
                break;

            case "vault.import.wizard":
                await this._vaultImportWizard();
                break;
        }

        return true;
    },

    /**
     * Add the required rpc service to the controller which will be used to
     * get/store information from/to the vault controller
     */
    setup() {
        if (this.props.resModel === "vault" && !utils.supported()) {
            this.props.preventCreate = true;
            this.props.preventEdit = true;
        }

        this._super(...arguments);
        this.rpc = useService("rpc");
    },

    /**
     * Hook into the relevant functions
     */
    async create() {
        const _super = this._super.bind(this);
        if (this.model.root.isDirty) await this._vaultAction();

        const ret = await _super(...arguments);
        return ret;
    },

    async onPagerUpdate() {
        const _super = this._super.bind(this);
        if (this.model.root.isDirty) await this._vaultAction();
        return await _super(...arguments);
    },

    async saveButtonClicked() {
        const _super = this._super.bind(this);
        if (this.model.root.isDirty) await this._vaultAction();
        return await _super(...arguments);
    },

    async beforeLeave() {
        const _super = this._super.bind(this);
        if (this.model.root.isDirty) await this._vaultAction();
        return await _super(...arguments);
    },

    async beforeUnload() {
        const _super = this._super.bind(this);
        if (this.model.root.isDirty) await this._vaultAction();
        return await _super(...arguments);
    },

    async beforeExecuteActionButton(clickParams) {
        const _super = this._super.bind(this);
        if (clickParams.special !== "cancel") {
            const _continue = await this._vaultAction(clickParams);
            if (!_continue) return false;
        }

        return await _super(...arguments);
    },
});

patch(ListController.prototype, "vault", {
    setup() {
        this._super(...arguments);
        if (this.props.resModel === "vault" && !utils.supported())
            this.props.showButtons = false;
    },
});
