// © 2021 Florian Kantelberg - initOS GmbH
// License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

odoo.define("vault.UserMenu", function (require) {
    "use strict";

    var UserMenu = require("web.UserMenu");

    UserMenu.include({
        _onMenuKeys: function () {
            var self = this;
            var session = this.getSession();
            this.trigger_up("clear_uncommitted_changes", {
                callback: function () {
                    self._rpc({
                        model: "res.users",
                        method: "action_get_vault",
                    }).then(function (result) {
                        result.res_id = session.uid;
                        self.do_action(result);
                    });
                },
            });
        },
    });
});
