odoo.define("auth_show_hide_password.login", function (require) {
    "use strict";

    var publicWidget = require("web.public.widget");
    var Login = publicWidget.registry.login;

    Login.include({
        events: _.extend({}, Login.prototype.events, {
            "click .show_hide_password": "_onClickBtnShowHidePassword",
        }),

        _onClickBtnShowHidePassword: function (ev) {
            var $eyeIcon = $(ev.currentTarget).find("i.fa");
            var inputID = $(ev.currentTarget).attr("data-input-id");
            if ($eyeIcon.hasClass("fa-eye")) {
                $eyeIcon.removeClass("fa-eye").addClass("fa-eye-slash");
                window.$(".oe_login_form input#" + inputID).prop("type", "text");
            } else if ($eyeIcon.hasClass("fa-eye-slash")) {
                $eyeIcon.removeClass("fa-eye-slash").addClass("fa-eye");
                window.$(".oe_login_form input#" + inputID).prop("type", "password");
            }
        },
    });
});
