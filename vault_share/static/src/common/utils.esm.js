/** @odoo-module alias=vault.share.utils **/
// © 2021-2022 Florian Kantelberg - initOS GmbH
// License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

const PinSize = 5;

import utils from "vault.utils";

function generate_pin(pin_size) {
    return utils.generate_secret(pin_size, "0123456789");
}

export default {
    PinSize: PinSize,
    generate_pin: generate_pin,
};
