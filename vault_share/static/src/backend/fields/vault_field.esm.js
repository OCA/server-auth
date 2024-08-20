/** @odoo-module **/
// © 2021-2024 Florian Kantelberg - initOS GmbH
// License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import VaultField from "vault.field";
import {_lt} from "@web/core/l10n/translation";
import {patch} from "@web/core/utils/patch";
import sh_utils from "vault.share.utils";
import utils from "vault.utils";
import vault from "vault";

// Extend the widget to share
patch(VaultField.prototype, "vault_share", {
    get shareButton() {
        return this.props.value;
    },
    /**
     * Share the value for an external user
     *
     * @private
     */
    async _onShareValue(ev) {
        ev.stopPropagation();
        const iv = await utils.generate_iv_base64();
        const pin = sh_utils.generate_pin(sh_utils.PinSize);
        const salt = utils.generate_bytes(utils.SaltLength).buffer;
        const key = await utils.derive_key(pin, salt, utils.Derive.iterations);
        const public_key = await vault.get_public_key();
        const value = await this._decrypt(this.props.value);

        this.action.doAction({
            type: "ir.actions.act_window",
            title: _lt("Share the secret"),
            target: "new",
            res_model: "vault.share",
            views: [[false, "form"]],
            context: {
                default_secret: await utils.sym_encrypt(key, value, iv),
                default_pin: await utils.asym_encrypt(
                    public_key,
                    pin + utils.generate_iv_base64()
                ),
                default_iterations: utils.Derive.iterations,
                default_iv: iv,
                default_salt: utils.toBase64(salt),
            },
        });
    },
});
