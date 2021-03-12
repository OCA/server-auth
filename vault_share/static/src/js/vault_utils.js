// © 2021 Florian Kantelberg - initOS GmbH
// License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

odoo.define("vault.share.utils", function (require) {
    "use strict";

    const PinSize = 5;

    var utils = require("vault.utils");

    function generate_pin(pin_size) {
        return utils.generate_secret(pin_size, "0123456789");
    }

    return {
        PinSize: PinSize,
        generate_pin: generate_pin,
    };
});
