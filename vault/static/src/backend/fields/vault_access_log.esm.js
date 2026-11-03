// © 2024 Odoo Community Association (OCA)
// License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import {VaultField} from "./vault_field.esm";
import {patch} from "@web/core/utils/patch";
import {rpc} from "@web/core/network/rpc";

// Audit every successful reveal/copy of a secret for NIS2 / ISO 27001.
// Only the record id and the access type are sent to the server -- never the
// decrypted plaintext. The originating IP is resolved server-side from the
// HTTP request, so it is intentionally not provided by the browser.
const logVaultAccess = async (resId, accessType) => {
    if (!resId) {
        return;
    }
    try {
        await rpc("/web/dataset/call_kw/vault.entry/action_log_access", {
            model: "vault.entry",
            method: "action_log_access",
            args: [[resId], accessType],
            kwargs: {},
        });
    } catch {
        // Auditing must never break the user-facing action.
    }
};

patch(VaultField.prototype, {
    async _onShowValue(ev) {
        const wasDecrypted = this.state.decrypted;
        await super._onShowValue(ev);
        // Only log the transition into the revealed state, not hiding it again.
        if (!wasDecrypted && this.state.decrypted) {
            await logVaultAccess(this.props.record.resId, "reveal");
        }
    },

    async _onCopyValue(ev) {
        await super._onCopyValue(ev);
        await logVaultAccess(this.props.record.resId, "copy");
    },
});
