//  Copyright 2018 Modoolar <info@modoolar.com>
//  License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
odoo.define("password_security.policy", function(require) {
    "use strict";

    let core = require("web.core");
    let _t = core._t;
    let auth_password_policy = require("auth_password_policy");
    let Policy = auth_password_policy.Policy;

    Policy.include({
        /**
         *
         * @param {Object} info
         * @param {Number} [info.password_length=4]
         * @param {Number} [info.password_lower=1]
         * @param {Number} [info.password_upper=1]
         * @param {Number} [info.password_numeric=1]
         * @param {Number} [info.password_special=1]
         * @param {Number} [info.password_estimate=3]
         */
        init: function(info) {
            this._super(info);

            this._password_length = info.password_length || 4;
            this._password_lower = info.password_lower || 1;
            this._password_upper = info.password_upper || 1;
            this._password_numeric = info.password_numeric || 1;
            this._password_special = info.password_special || 1;
            this._password_estimate = info.password_estimate || 3;
        },

        toString: function() {
            let msgs = [];
            let msg_common = _t("at least ")

            if (this._password_length > 0) {
                 let msg_password_length = msg_common + this._password_length + _t(" characters")
                msgs.push(
                    msg_password_length
                );
            }

            if (this._password_lower > 0) {
                let msg_password_lower = msg_common + this._password_lower + _t(" lower case characters")
                msgs.push(
                        msg_password_lower
                );
            }

            if (this._password_upper > 0) {
                let msg_password_upper = msg_common + this._password_lower + _t(" upper case characters")
                msgs.push(
                    msg_password_upper
                );
            }

            if (this._password_numeric > 0) {
                let msg_password_numeric = msg_common + this._password_lower + _t(" numeric characters")
                msgs.push(
                    msg_password_numeric
                );
            }

            if (this._password_special > 0) {
                let msg_password_special = msg_common + this._password_lower + _t(" special characters")
                msgs.push(
                    msg_password_special
                );
            }

            return msgs.join(", ");
        },

        _calculate_password_score: function(pattern, min_count, password) {
            let matchMinCount = new RegExp(
                "(.*" + pattern + ".*){" + min_count + ",}",
                "g"
            ).exec(password);
            if (matchMinCount === null) {
                return 0;
            }

            let count = 0;
            let regExp = new RegExp(pattern, "g");

            while (regExp.exec(password) !== null) {
                count++;
            }

            return Math.min(count / min_count, 1.0);
        },

        _estimate: function(password) {
            let zxcvbn = window.zxcvbn;
            return Math.min(zxcvbn(password).score / 4.0, 1.0);
        },

        score: function(password) {
            let lengthscore = Math.min(password.length / this._password_length, 1.0);
            let loverscore = this._calculate_password_score(
                "[a-z]",
                this._password_lower,
                password
            );
            let upperscore = this._calculate_password_score(
                "[A-Z]",
                this._password_upper,
                password
            );
            let numericscore = this._calculate_password_score(
                "\\d",
                this._password_numeric,
                password
            );
            let specialscore = this._calculate_password_score(
                "[\\W_]",
                this._password_special,
                password
            );
            let estimatescore = this._estimate(password);

            return (
                lengthscore *
                loverscore *
                upperscore *
                numericscore *
                specialscore *
                estimatescore
            );
        },
    });

    let recommendations = {
        score: auth_password_policy.recommendations.score,
        policies: [
            new Policy({
                password_length: 12,
                password_upper: 3,
                password_lower: 3,
                password_numeric: 3,
                password_special: 3,
                password_estimate: 3,
            }),
            new Policy({
                password_length: 16,
                password_upper: 4,
                password_lower: 4,
                password_numeric: 4,
                password_special: 4,
                password_estimate: 4,
            }),
        ],
    };

    auth_password_policy.recommendations = recommendations;
});
