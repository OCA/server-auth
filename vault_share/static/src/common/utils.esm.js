// © 2021-2024 Florian Kantelberg - initOS GmbH
// License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import utils from "@vault/common/utils.esm";

const PinSize = 5;

function generate_pin(pin_size) {
    return utils.generate_secret(pin_size, "0123456789");
}

export default {
    PinSize: PinSize,
    generate_pin: generate_pin,
};
