/** @odoo-module **/

import tour from 'web_tour.tour';

/**
 * This tour depends on data created by python test in charge of launching it.
 * It is not intended to work when launched from interface.
 * @see auth_password_pwned/tests/test_auth_password_pwned.py
 */
tour.register('auth_password_pwned/static/tests/tours/change_password_test_tour_pwned.js', {
    test: true,
}, [{
    content: "Open Settings",
    trigger: ".o_app.o_menuitem:contains('Settings')",
}, {
    content: "Open Users & Companies Dropdown",
    trigger: ".o_main_navbar .o_menu_sections .o-dropdown:contains('Users & Companies') button",
}, {
    content: "Open Users Lists",
    trigger: ".o_main_navbar .o_menu_sections .o-dropdown:contains('Users & Companies') .dropdown-item:contains('Users')",
}, {
    content: "Wait for users list to start loading",
    trigger: "body:contains('Loading')",
    run: () => null,
}, {
    content: "Wait for loaded users list",
    trigger: "body:not(:contains('Loading'))",
    run: () => null,
}, {
    content: "Select Demo User",
    trigger: ".o_content tr:contains('Demo') .o_list_record_selector",
}, {
    content: "Wait for Demo User to be selected",
    trigger: ".o_content tr:contains('Demo') input[type='checkbox']:checked",
    run: () => null,
}, {
    content: "Open Actions Menu",
    trigger: ".o_action_manager button:contains('Action')",
}, {
    content: "Open Change Passwords Dialog",
    trigger: ".o_action_manager .dropdown.show a.dropdown-item:contains('Change Password')",
}, {
    content: "Enable input for setting Pwned Password",
    trigger: ".modal-content tr:contains('demo')",
    run: function(actions) {
        var i=0;
        while(this.$anchor.find("input[name='new_passwd']").length <= 0) {
            actions.click(this.$anchor.find("div"));
            i++;
            if (i > 1000) assert(false);
        }
    }
}, {
    content: "Set Pwned Password",
    trigger: ".modal-content tr:contains('demo') input[name='new_passwd']",
    run: "text demo",
}, {
    content: "Change Password",
    trigger: ".modal-footer btn-primary",
}, {
    //TODO verify that alert is shown
}]);
