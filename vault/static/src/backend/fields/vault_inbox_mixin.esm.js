// © 2021-2024 Florian Kantelberg - initOS GmbH
// License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import {_t} from "@web/core/l10n/translation";
import {useService} from "@web/core/utils/hooks";

export default (x) => {
    class Extended extends x {
        static props = {
            ...x.props,
            storeModel: {type: String, optional: true},
        };
        static extractProps = ({attrs}) => {
            return {
                storeModel: attrs.store,
            };
        };
        setup() {
            super.setup();

            if (!this.action) this.action = useService("action");
            this.vault_utils = useService("vault_utils");
            this.vault = useService("vault");
        }

        /**
         * Save the content in an entry of a vault
         *
         * @private
         * @param {String} model
         * @param {String} value
         * @param {String} name
         */
        async saveValue(model, value, name = "") {
            const key = await this.vault_utils.generate_key();
            const iv = this.vault_utils.generate_iv_base64();
            const decrypted = await this._decrypt(value);

            this.action.doAction({
                type: "ir.actions.act_window",
                title: _t("Store the secret in a vault"),
                target: "new",
                res_model: "vault.store.wizard",
                views: [[false, "form"]],
                context: {
                    default_model: model,
                    default_secret_temporary: await this.vault_utils.sym_encrypt(
                        key,
                        decrypted,
                        iv
                    ),
                    default_name: name,
                    default_iv: iv,
                    default_key: await this.vault.wrap(key),
                },
            });
        }
    }

    return Extended;
};
