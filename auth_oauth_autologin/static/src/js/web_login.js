odoo.define("auth_oauth_autologin.redirect", function(require) {
    "use strict";

    var publicWidget = require("web.public.widget");

    publicWidget.registry.authOauthAutologinWidget = publicWidget.Widget.extend({
        selector: ".oe_login_form",

        /**
         * @override
         */
        start: function() {
            const def = this._super.apply(this, arguments);
            let url = window.location.href;
            if (url.includes("/web/login")) {
                url = url.replace("/web/login", "/web");
            }
            $.blockUI();
            this._rpc({
                route: "/auth/auto_login_redirect_link",
                params: {
                    redirect: url,
                },
            }).then(function(result) {
                if (result) {
                    window.location = result;
                }
                $.unblockUI();
            });
            return def;
        },
    });
});
