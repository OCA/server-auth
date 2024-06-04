/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.login.include({
    selector: ".oe_login_form",
    init() {
        this._super(...arguments);
        this._rpc = this.bindService("rpc");
    },

    start: async function () {
        const def = this._super.apply(this, arguments);
        let url = window.location.href;
        if (url.includes("/web/login")) {
            url = url.replace("/web/login", "/web");
        }
        this._result = await this._rpc("/auth/auto_login_redirect_link", {
            redirect: url,
        });
        if (this._result) {
            window.location = this._result;
        }
        return def;
    },
});
