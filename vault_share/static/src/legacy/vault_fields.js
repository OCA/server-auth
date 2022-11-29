// © 2021 Florian Kantelberg - initOS GmbH
// License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

odoo.define("vault.share.fields", function (require) {
    "use strict";

    const core = require("web.core");
    const sh_utils = require("vault.share.utils");
    const utils = require("vault.utils");
    const vault = require("vault");
    const vault_fields = require("vault.fields");

    const _t = core._t;

    // Extend the widget to share
    vault_fields.VaultField.include({
        events: _.extend(vault_fields.VaultField.prototype.events, {
            "click .o_vault_share": "_onShareValue",
        }),

        /**
         * Share the value for an external user
         *
         * @private
         * @param {OdooEvent} ev
         */
        _onShareValue: async function (ev) {
            ev.stopPropagation();

            const iv = await utils.generate_iv_base64();
            const pin = sh_utils.generate_pin(sh_utils.PinSize);
            const salt = utils.generate_bytes(utils.SaltLength).buffer;
            const key = await utils.derive_key(pin, salt, 4000);
            const public_key = await vault.get_public_key();
            const value = await this._decrypt(this.value);

            this.do_action({
                type: "ir.actions.act_window",
                title: _t("Share the secret"),
                target: "new",
                res_model: "vault.share",
                views: [[false, "form"]],
                context: {
                    default_secret: await utils.sym_encrypt(key, value, iv),
                    default_pin: await utils.asym_encrypt(
                        public_key,
                        pin + utils.generate_iv_base64()
                    ),
                    default_iv: iv,
                    default_salt: utils.toBase64(salt),
                },
            });
        },
    });
});
