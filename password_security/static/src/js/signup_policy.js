//  Copyright 2018 Modoolar <info@modoolar.com>
//  License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
odoo.define('password_security.signup.policy', function (require) {
    "use strict";

    var base = require('web_editor.base');
    var policy = require('auth_password_policy');
    var PasswordMeter = require('auth_password_policy.Meter');

    base.ready().then(function () {
        var $signupForm = $('.oe_signup_form, .oe_reset_password_form');
        if (!$signupForm.length) {
            return;
        }

        var $password = $signupForm.find('#password');
        var password_length = Number($password.attr('password_length'));
        var password_lower = Number($password.attr('password_lower'));
        var password_upper = Number($password.attr('password_upper'));
        var password_numeric = Number($password.attr('password_numeric'));
        var password_special = Number($password.attr('password_special'));
        var password_estimate = Number($password.attr('password_estimate'));

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
        meter.insertAfter($password);
        $password.on('input', function () {
            meter.update($password.val());
        });
    });
});
