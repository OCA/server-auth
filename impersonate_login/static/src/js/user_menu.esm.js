/** @odoo-module **/
// License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import {_t} from "@web/core/l10n/translation";
import {registry} from "@web/core/registry";
import {session} from "@web/session";
import {markup} from "@odoo/owl";

export function impersonateLoginItem(env) {
    return {
        type: "item",
        id: "impersonate_login",
        description: _t("Switch Login"),
        hide: session.impersonate_from_uid || !session.is_impersonate_user,
        callback: async function () {
            const actionImpersonateLogin = await env.services.orm.call(
                "res.users",
                "action_impersonate_login"
            );
            // Ensure help (if containing HTML) renders as markup, like /web/action/load path
            if (
                actionImpersonateLogin &&
                typeof actionImpersonateLogin.help === "string"
            ) {
                actionImpersonateLogin.help = markup(actionImpersonateLogin.help);
            }
            env.services.action.doAction(actionImpersonateLogin);
        },
        sequence: 55,
    };
}

export function impersonateBackLoginItem(env) {
    return {
        type: "item",
        id: "impersonate_back",
        description: _t("Back to Original User"),
        hide: !session.impersonate_from_uid,
        callback: async function () {
            const actionBackToOriginLogin = await env.services.orm.call(
                "res.users",
                "back_to_origin_login"
            );
            env.services.action.doAction(actionBackToOriginLogin);
        },
        sequence: 55,
    };
}

registry
    .category("user_menuitems")
    .add("impersonate_login", impersonateLoginItem, {force: true})
    .add("impersonate_back", impersonateBackLoginItem, {force: true});
