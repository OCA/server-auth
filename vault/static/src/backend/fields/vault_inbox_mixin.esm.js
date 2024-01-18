/** @odoo-module alias=vault.inbox.mixin **/
// © 2021-2024 Florian Kantelberg - initOS GmbH
// License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import {_lt} from "@web/core/l10n/translation";
import {useService} from "@web/core/utils/hooks";
import utils from "vault.utils";
import vault from "vault";

export default (x) => {
    class Extended extends x {
        setup() {
            super.setup();

            if (!this.action) this.action = useService("action");
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
            const key = await utils.generate_key();
            const iv = utils.generate_iv_base64();
            const decrypted = await this._decrypt(value);

            this.action.doAction({
                type: "ir.actions.act_window",
                title: _lt("Store the secret in a vault"),
                target: "new",
                res_model: "vault.store.wizard",
                views: [[false, "form"]],
                context: {
                    default_model: model,
                    default_secret_temporary: await utils.sym_encrypt(
                        key,
                        decrypted,
                        iv
                    ),
                    default_name: name,
                    default_iv: iv,
                    default_key: await vault.wrap(key),
                },
            });
        }
    }

    Extended.props = {
        ...x.props,
        storeModel: {type: String, optional: true},
    };

    Extended.extractProps = ({attrs}) => {
        return {
            storeModel: attrs.store,
        };
    };

    return Extended;
};
