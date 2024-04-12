odoo.define("auth_show_hide_password.signup", function (require) {
    "use strict";

    var publicWidget = require("web.public.widget");
    require("auth_signup.signup");
    var SignUpForm = publicWidget.registry.SignUpForm;

    SignUpForm.include({
        events: _.extend({}, SignUpForm.prototype.events, {
            "click .show_hide_password": "_onClickBtnShowHidePassword",
        }),

        _onClickBtnShowHidePassword: function (ev) {
            var $eyeIcon = $(ev.currentTarget).find("i.fa");
            var inputID = $(ev.currentTarget).attr("data-input-id");
            if ($eyeIcon.hasClass("fa-eye")) {
                $eyeIcon.removeClass("fa-eye").addClass("fa-eye-slash");
                window.$(".oe_signup_form input#" + inputID).prop("type", "text");
            } else if ($eyeIcon.hasClass("fa-eye-slash")) {
                $eyeIcon.removeClass("fa-eye-slash").addClass("fa-eye");
                window.$(".oe_signup_form input#" + inputID).prop("type", "password");
            }
        },
    });
});
