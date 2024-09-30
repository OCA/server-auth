/** @odoo-module **/

import tour from 'web_tour.tour';

/**
 * This tour depends on data created by python test in charge of launching it.
 * It is not intended to work when launched from interface.
 * @see auth_password_pwned/tests/test_auth_password_pwned.py
 */
tour.register('auth_password_pwned/static/tests/tours/login_test_tour_ok.js', {
    test: true,
}, [{
    content: "Set login",
    trigger: ".oe_login_form #login",
    run: "text testuser",
}, {
    content: "Set password",
    trigger: ".oe_login_form #password",
    run: "text testuser",
}, {
    content: "Login to backend",
    trigger: ".oe_login_form button[type='submit']",
}, {
    content: "Check that backend is loading",
    trigger: ".o_web_client",
    // We are checking the error message here
    run: () => null,
}]);
