// © 2021-2024 Florian Kantelberg - initOS GmbH
// License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import {Component, useEffect, useRef, useState} from "@odoo/owl";
import {useBus, useService} from "@web/core/utils/hooks";
import VaultMixin from "./vault_mixin.esm";
import {_t} from "@web/core/l10n/translation";
import {getActiveHotkey} from "@web/core/hotkeys/hotkey_service";
import {registry} from "@web/core/registry";

export class VaultField extends VaultMixin(Component) {
    static template = "vault.FieldVault";
    setup() {
        super.setup();

        this.action = useService("action");
        this.input = useRef("input");
        this.span = useRef("span");
        this.state = useState({
            decrypted: false,
            decryptedValue: "",
            isDirty: false,
            lastSetValue: null,
        });

        const self = this;
        useEffect(
            (inputEl) => {
                if (inputEl) {
                    const onInput = self.onInput.bind(self);
                    const onKeydown = self.onKeydown.bind(self);

                    inputEl.addEventListener("input", onInput);
                    inputEl.addEventListener("keydown", onKeydown);
                    return () => {
                        inputEl.removeEventListener("input", onInput);
                        inputEl.removeEventListener("keydown", onKeydown);
                    };
                }
            },
            () => [self.input.el]
        );

        useEffect(() => {
            const isInvalid = self.props.record
                ? self.props.record.isFieldInvalid(self.props.name)
                : false;

            if (self.input.el && !self.state.isDirty && !isInvalid) {
                Promise.resolve(self.getValue()).then((val) => {
                    if (!self.input.el) return;

                    if (val) self.input.el.value = val;
                    else if (val !== "")
                        self.props.record.setInvalidField(self.props.name);
                });
                self.state.lastSetValue = self.input.el.value;
            }
        });
        const {model} = this.props.record;
        useBus(model.bus, "WILL_SAVE_URGENTLY", () => self.commitChanges(true));
        useBus(model.bus, "NEED_LOCAL_CHANGES", (ev) =>
            ev.detail.proms.push(self.commitChanges())
        );
        useBus(model.bus, "ENCRYPT_FIELDS", () => {
            this.state.decrypted = false;
            this.showValue();
        });
    }

    get value() {
        return this.props.record.data[this.props.name];
    }

    /**
     * Open a dialog to generate a new secret
     *
     * @param {Object} ev
     */
    async _onGenerateValue(ev) {
        ev.stopPropagation();

        const password = await this.vault_utils.generate_pass();
        await this.storeValue(password);
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
     * Send the secret to an inbox of an user
     *
     * @param {Object} ev
     */
    async _onSendValue(ev) {
        ev.stopPropagation();

        await this.sendValue(this.value, "");
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
     * Decrypt the value of the field
     *
     * @returns decrypted value
     */
    async getValue() {
        return await this._decrypt(this.value);
    }

    /**
     * Update the value shown
     */
    async showValue() {
        this.span.el.innerHTML = this.formattedValue;
    }

    /**
     * Handle input event and set the state to dirty
     *
     * @param {Object} ev
     */
    onInput(ev) {
        ev.stopPropagation();
        this.state.isDirty = ev.target.value !== this.state.lastSetValue;
        if (this.state.isDirty)
            this.props.record.model.bus.trigger("FIELD_IS_DIRTY", this.state.isDirty);
    }

    /**
     * Commit the changes of the input field to the record
     *
     * @param {Boolean} urgent
     */
    async commitChanges(urgent) {
        if (!this.input.el) return;

        this.state.isDirty = this.input.el.value !== this.state.lastSetValue;
        if (this.state.isDirty || urgent) {
            this.state.isDirty = false;

            const val = this.input.el.value || false;
            if (val !== (this.state.lastSetValue || false)) {
                this.state.lastSetValue = this.input.el.value;
                this.state.decryptedValue = this.input.el.value;
                await this.storeValue(val);
                this.props.record.model.bus.trigger(
                    "FIELD_IS_DIRTY",
                    this.state.isDirty
                );
            }
        }
    }

    /**
     * Handle keyboard events and trigger changes
     *
     * @param {Object} ev
     */
    onKeydown(ev) {
        ev.stopPropagation();

        const hotkey = getActiveHotkey(ev);
        if (["enter", "tab", "shift+tab"].includes(hotkey)) this.commitChanges(false);
    }
}

export const vaultField = {
    component: VaultField,
    displayName: _t("Vault Field"),
    supportedTypes: ["char"],
};

registry.category("fields").add("vault_field", vaultField);
