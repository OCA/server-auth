// © 2021-2022 Florian Kantelberg - initOS GmbH
// License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import {_t} from "@web/core/l10n/translation";
import {registry} from "@web/core/registry";
import {user} from "@web/core/user";

export function vaultPreferencesItem(env) {
    return {
        type: "item",
        id: "key_management",
        description: _t("Key Management"),
        callback: async function () {
            const actionDescription = await env.services.orm.call(
                "res.users",
                "action_get_vault"
            );
            actionDescription.res_id = user.userId;
            env.services.action.doAction(actionDescription);
        },
        sequence: 55,
    };
}

registry
    .category("user_menuitems")
    .add("vault_key_management", vaultPreferencesItem, {force: true});
