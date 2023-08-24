/** @odoo-module */

import { registry } from '@web/core/registry';
import { formView } from '@web/views/form/form_view';
import { FormController } from '@web/views/form/form_controller';
import { ConfirmationDialog, AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { useService } from "@web/core/utils/hooks";

import { supported } from 'vault.utils';
import vault  from "vault";

export class VaultFormController extends FormController {

    setup() {
        super.setup();
        this.dialog = useService("dialog");
        this.rpc = useService("rpc");
    }
    /**
     * @override
     */
    async beforeExecuteActionButton(clickParams) {
        if (clickParams.name === 'action_generate_key' && this.props.resModel == "res.users") {
            this._onGenerateKeys()
            return false;
        }
        return super.beforeExecuteActionButton(clickParams);
    }
    /**
     * Generate a new key pair and re-encrypt the master keys of the vaults
     *
     * @private
     * @param {OdooEvent} ev
     */
    async _onGenerateKeys() {
        if (!supported()) return;

        this.dialog.add(ConfirmationDialog, {
            title: this.env._t("Generate New Keys"),
            body: this.env._t("Do you really want to create a new key pair and set it active?"),
            confirm: this._newVaultKeyPair.bind(this),
        });
    }
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
        const master_keys = await this.rpc("/vault/rights/get", {});
        let result = {};
        for (const uuid in master_keys) {
            result[uuid] = await utils.wrap(
                await utils.unwrap(master_keys[uuid], private_key),
                public_key
            );
        }

        await this.rpc("/vault/rights/store", {keys: result});

        // Re-encrypt the inboxes to not loose it
        const inbox_keys = await this.rpc("/vault/inbox/get", {});
        result = {};
        for (const uuid in inbox_keys) {
            result[uuid] = await utils.wrap(
                await utils.unwrap(inbox_keys[uuid], private_key),
                public_key
            );
        }

        await this.rpc("/vault/inbox/store",{ keys: result});

        // await this.reload(); TODO: Search new function name
    }
}

registry.category('views').add('vault_form_view', {
    ...formView,
    Controller: VaultFormController,
});
