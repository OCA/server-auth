/** @odoo-module **/

import tour from 'web_tour.tour';

/**
 * This tour depends on data created by python test in charge of launching it.
 * It is not intended to work when launched from interface.
 * @see auth_password_pwned/tests/test_auth_password_pwned.py
 */
tour.register('auth_password_pwned/static/tests/tours/login_test_tour_pwned.js', {
    test: true,
}, [{
    content: "Set login",
    trigger: ".oe_login_form #login",
    run: "text testpassword",
}, {
    content: "Set password",
    trigger: ".oe_login_form #password",
    run: "text testpassword",
}, {
    content: "Try to login to backend",
    trigger: ".oe_login_form button[type='submit']",
}, {
    content: "Check that there is a warning for an unsafe password",
    trigger: ".oe_login_form .alert:contains('This password is known by third parties an email has been sent with instructions how to reset it.')",
    // We are checking the error message here
    run: () => null,
}]);
