// License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import {markup, usePlugin} from "@odoo/owl";
import {ORM} from "@web/core/orm_plugin";
import {_t} from "@web/core/l10n/translation";
import {registry} from "@web/core/registry";
import {session} from "@web/session";
import {useService} from "@web/core/utils/hooks";

export function impersonateLoginItem() {
    const action = useService("action");
    const orm = usePlugin(ORM);
    return {
        type: "item",
        id: "impersonate_login",
        description: _t("Switch Login"),
        hide: session.impersonate_from_uid || !session.is_impersonate_user,
        callback: async function () {
            const actionImpersonateLogin = await orm.call(
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
            action.doAction(actionImpersonateLogin);
        },
        sequence: 55,
    };
}

export function impersonateBackLoginItem() {
    const action = useService("action");
    const orm = usePlugin(ORM);
    return {
        type: "item",
        id: "impersonate_back",
        description: _t("Back to Original User"),
        hide: !session.impersonate_from_uid,
        callback: async function () {
            const actionBackToOriginLogin = await orm.call(
                "res.users",
                "back_to_origin_login"
            );
            action.doAction(actionBackToOriginLogin);
        },
        sequence: 55,
    };
}

registry
    .category("user_menuitems")
    .add("impersonate_login", impersonateLoginItem, {force: true})
    .add("impersonate_back", impersonateBackLoginItem, {force: true});
