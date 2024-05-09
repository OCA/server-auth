//  Copyright 2018 Modoolar <info@modoolar.com>
//  License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
odoo.define("password_security.signup.policy", function (require) {
    "use strict";

    var policy = require("auth_password_policy");
    var PasswordMeter = require("auth_password_policy.Meter");
    // Wait until auth_password_policy_signup.policy is done
    require("auth_password_policy_signup.policy");

    var $signupForm = $(".oe_signup_form, .oe_reset_password_form");
    if (!$signupForm.length) {
        return;
    }

    var $password = $signupForm.find("#password");
    var password_length = Number($password.attr("passwordlength"));
    var password_lower = Number($password.attr("passwordlower"));
    var password_upper = Number($password.attr("passwordupper"));
    var password_numeric = Number($password.attr("passwordnumeric"));
    var password_special = Number($password.attr("passwordspecial"));
    var password_estimate = Number($password.attr("passwordestimate"));

    var meter = new PasswordMeter(
        null,
        new policy.Policy({
            password_length: password_length,
            password_lower: password_lower,
            password_upper: password_upper,
            password_numeric: password_numeric,
            password_special: password_special,
            password_estimate: password_estimate,
        }),
        policy.recommendations
    );
    // Remove the old meter
    $password.parent().find("meter").remove();
    meter.insertAfter($password);
    $password.on("input", function () {
        meter.update($password.val());
    });
});
