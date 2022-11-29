/** @odoo-module **/
// © 2021-2022 Florian Kantelberg - initOS GmbH
// License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import {registry} from "@web/core/registry";

export function vaultPreferencesItem(env) {
    return {
        type: "item",
        id: "key_management",
        description: env._t("Key Management"),
        callback: async function () {
            const actionDescription = await env.services.orm.call(
                "res.users",
                "action_get_vault"
            );
            actionDescription.res_id = env.services.user.userId;
            env.services.action.doAction(actionDescription);
        },
        sequence: 55,
    };
}

registry.category("user_menuitems").add("key", vaultPreferencesItem, {force: true});
