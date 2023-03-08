odoo.define("password_security.auth_password_policy_tests", function (require) {
    "use strict";

    /* global QUnit */

    var Policy = require("auth_password_policy").Policy;

    QUnit.module("auth_password_policy", {}, function () {
        QUnit.test("Policy.score", async function (assert) {
            var info = {
                password_length: 4,
                password_upper: 1,
                password_lower: 1,
                password_numeric: 1,
                password_special: 1,
                password_estimate: 3,
            };

            var base = new Policy(info);
            assert.ok(base.score("aB3!") > 0, "pass: " + base.toString());

            var policy = new Policy(_.extend({}, info, {password_lower: 0}));
            assert.ok(policy.score("AB3!") > 0, "pass: " + policy.toString());
            assert.equal(base.score("AB3!"), 0, "fail: " + base.toString());

            policy = new Policy(_.extend({}, info, {password_numeric: 0}));
            assert.ok(policy.score("aBc!") > 0, "pass: " + policy.toString());
            assert.equal(base.score("aBc!"), 0, "fail: " + base.toString());

            policy = new Policy(_.extend({}, info, {password_special: 0}));
            assert.ok(policy.score("aB3d") > 0, "pass: " + policy.toString());
            assert.equal(base.score("aB3d"), 0, "fail: " + base.toString());

            policy = new Policy(_.extend({}, info, {password_upper: 0}));
            assert.ok(policy.score("ab3!") > 0, "pass: " + policy.toString());
            assert.equal(base.score("ab3!"), 0, "fail: " + base.toString());
        });
    });
});
