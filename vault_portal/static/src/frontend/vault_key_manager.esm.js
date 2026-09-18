// Copyright 2026 INVITU (<https://www.invitu.com>)
// License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import {Component, useState} from "@odoo/owl";
import {ConfirmationDialog} from "@web/core/confirmation_dialog/confirmation_dialog";
import {_t} from "@web/core/l10n/translation";
import {registry} from "@web/core/registry";
import {useService} from "@web/core/utils/hooks";
import {user} from "@web/core/user";

export class VaultKeyManager extends Component {
    static template = "vault_portal.VaultKeyManager";
    static props = {hasKeys: Boolean};

    setup() {
        this.vault = useService("vault");
        this.orm = useService("orm");
        this.dialog = useService("dialog");
        this.state = useState({busy: false, error: null, done: false});
    }

    async onSetupKey() {
        this.state.error = null;
        this.state.busy = true;
        try {
            await this.vault.get_private_key();
            this.state.done = true;
        } catch (err) {
            console.error(err);
            this.state.error = _t("Could not set up your key.");
        } finally {
            this.state.busy = false;
        }
    }

    async onInvalidateKey() {
        const confirmed = await new Promise((resolve) => {
            this.dialog.add(ConfirmationDialog, {
                title: _t("Invalidate key"),
                body: _t(
                    "You will lose access to all vaults until a technician grants it again with your new key. Continue?"
                ),
                confirm: () => resolve(true),
                cancel: () => resolve(false),
            });
        });
        if (!confirmed) {
            return;
        }
        // Action_invalidate_key(self) is bound to a recordset: the ids
        // list must be the first element of args (Odoo's call_kw
        // convention), not the userId directly.
        await this.orm.call("res.users", "action_invalidate_key", [[user.userId]]);
        window.location.reload();
    }
}

registry
    .category("public_components")
    .add("vault_portal.vault_key_manager", VaultKeyManager);
