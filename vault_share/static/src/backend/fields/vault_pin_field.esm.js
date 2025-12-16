// © 2021-2024 Florian Kantelberg - initOS GmbH
// License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import {Component, useRef, useState} from "@odoo/owl";
import VaultMixin from "@vault/backend/fields/vault_mixin.esm";
import {_t} from "@web/core/l10n/translation";
import {registry} from "@web/core/registry";
import sh_utils from "../../common/utils.esm";
import {useService} from "@web/core/utils/hooks";

export class VaultPinField extends VaultMixin(Component) {
    static template = "vault.FieldPinVault";
    setup() {
        super.setup();

        this.action = useService("action");
        this.span = useRef("span");
        this.state = useState({
            decrypted: false,
            decryptedValue: "",
        });

        this.context = this.env.searchModel.context;
        this.props.readonly = true;
    }

    get sendButton() {
        return false;
    }
    get generateButton() {
        return false;
    }
    get saveButton() {
        return false;
    }
    get value() {
        return this.props.record.data[this.props.name];
    }

    /**
     * Get the decrypted value or a placeholder
     *
     * @returns the decrypted value or a placeholder
     */
    get formattedValue() {
        if (!this.value) return "";
        if (this.state.decrypted) return this.state.decryptedValue || "*******";
        return "*******";
    }

    /**
     * Decrypt the value using the private key of the vault and slice it to
     * the actual pin size because there is a salt following
     *
     * @private
     * @param {String} data
     * @returns the decrypted data
     */
    async _decrypt(data) {
        if (!data) return data;

        const pin_size = this.context.pin_size || sh_utils.PinSize;

        const private_key = await this.vault.get_private_key();
        const plain = await this.vault_utils.asym_decrypt(private_key, data);
        return plain.slice(0, pin_size);
    }

    /**
     * Copy the decrypted secret to the clipboard
     *
     * @param {Object} ev
     */
    async _onCopyValue(ev) {
        ev.stopPropagation();

        const value = await this._decrypt(this.value);
        await navigator.clipboard.writeText(value);
    }

    /**
     * Toggle between visible and invisible secret
     *
     * @param {Object} ev
     */
    async _onShowValue(ev) {
        ev.stopPropagation();

        this.state.decrypted = !this.state.decrypted;
        if (this.state.decrypted) {
            this.state.decryptedValue = await this._decrypt(this.value);
        } else {
            this.state.decryptedValue = "";
        }

        await this.showValue();
    }

    /**
     * Update the value shown
     */
    async showValue() {
        this.span.el.innerHTML = this.formattedValue;
    }
}

export const vaultPinField = {
    component: VaultPinField,
    displayName: _t("Vault Pin Field"),
    supportedTypes: ["char"],
};

registry.category("fields").add("vault_pin", vaultPinField);
