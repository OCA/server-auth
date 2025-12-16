// © 2021-2024 Florian Kantelberg - initOS GmbH
// License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import {VaultField} from "@vault/backend/fields/vault_field.esm";
import {_t} from "@web/core/l10n/translation";
import {patch} from "@web/core/utils/patch";
import sh_utils from "../../common/utils.esm";

// Extend the widget to share
patch(VaultField.prototype, {
    get shareButton() {
        return this.value;
    },
    /**
     * Share the value for an external user
     *
     * @private
     */
    async _onShareValue(ev) {
        ev.stopPropagation();
        const iv = await this.vault_utils.generate_iv_base64();
        const pin = sh_utils.generate_pin(sh_utils.PinSize);
        const salt = this.vault_utils.generate_bytes(
            this.vault_utils.SaltLength
        ).buffer;
        const key = await this.vault_utils.derive_key(
            pin,
            salt,
            this.vault_utils.Derive.iterations
        );
        const public_key = await this.vault.get_public_key();
        const value = await this._decrypt(this.value);

        this.action.doAction({
            type: "ir.actions.act_window",
            title: _t("Share the secret"),
            target: "new",
            res_model: "vault.share",
            views: [[false, "form"]],
            context: {
                default_secret: await this.vault_utils.sym_encrypt(key, value, iv),
                default_pin: await this.vault_utils.asym_encrypt(
                    public_key,
                    pin + this.vault_utils.generate_iv_base64()
                ),
                default_iterations: this.vault_utils.Derive.iterations,
                default_iv: iv,
                default_salt: this.vault_utils.toBase64(salt),
            },
        });
    },
});
