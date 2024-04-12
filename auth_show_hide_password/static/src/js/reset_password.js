odoo.define("auth_show_hide_password.reset_password", function (require) {
    "use strict";

    var publicWidget = require("web.public.widget");

    // Make a new widget because publicWidget.registry.SignUpForm
    // does not include .oe_reset_password_form selector
    publicWidget.registry.ResetPasswordShowHidePassword = publicWidget.Widget.extend({
        selector: ".oe_reset_password_form",
        events: {
            "click .show_hide_password": "_onClickBtnShowHidePassword",
        },

        _onClickBtnShowHidePassword: function (ev) {
            var $eyeIcon = $(ev.currentTarget).find("i.fa");
            // Find the input by id from window in order to avoid conflicts
            // with conditional elements like password meter
            var inputID = $(ev.currentTarget).attr("data-input-id");
            if ($eyeIcon.hasClass("fa-eye")) {
                $eyeIcon.removeClass("fa-eye").addClass("fa-eye-slash");
                window
                    .$(".oe_reset_password_form input#" + inputID)
                    .prop("type", "text");
            } else if ($eyeIcon.hasClass("fa-eye-slash")) {
                $eyeIcon.removeClass("fa-eye-slash").addClass("fa-eye");
                window
                    .$(".oe_reset_password_form input#" + inputID)
                    .prop("type", "password");
            }
        },
    });
});
