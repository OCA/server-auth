/** @odoo-module **/
// © 2021-2024 Florian Kantelberg - initOS GmbH
// License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import {Component, useRef, useState} from "@odoo/owl";
import VaultMixin from "vault.mixin";
import {_lt} from "@web/core/l10n/translation";
import {registry} from "@web/core/registry";
import sh_utils from "vault.share.utils";
import {useService} from "@web/core/utils/hooks";
import utils from "vault.utils";
import vault from "vault";

export default class VaultPinField extends VaultMixin(Component) {
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

    /**
     * Get the decrypted value or a placeholder
     *
     * @returns the decrypted value or a placeholder
     */
    get formattedValue() {
        if (!this.props.value) return "";
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

        const private_key = await vault.get_private_key();
        const plain = await utils.asym_decrypt(private_key, data);
        return plain.slice(0, pin_size);
    }

    /**
     * Copy the decrypted secret to the clipboard
     *
     * @param {Object} ev
     */
    async _onCopyValue(ev) {
        ev.stopPropagation();

        const value = await this._decrypt(this.props.value);
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
            this.state.decryptedValue = await this._decrypt(this.props.value);
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

VaultPinField.displayName = _lt("Vault Pin Field");
VaultPinField.supportedTypes = ["char"];
VaultPinField.template = "vault.FieldPinVault";

registry.category("fields").add("vault_pin", VaultPinField);
