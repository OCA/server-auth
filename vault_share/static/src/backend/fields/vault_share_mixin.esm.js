/** @odoo-module alias=vault.share.mixin **/
// © 2021-2024 Florian Kantelberg - initOS GmbH
// License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import sh_utils from "vault.share.utils";
import utils from "vault.utils";
import vault from "vault";

export default (x) => {
    class Extended extends x {
        setup() {
            super.setup();

            this.context = this.env.searchModel.context;
        }

        get shareButton() {
            return false;
        }
        get sendButton() {
            return false;
        }
        get isNew() {
            return this.props.record.isNew;
        }

        /**
         * Encrypt the pin with a random salt to make it hard to guess him by
         * encrypting every possilbilty with the public key. Store the pin in the
         * proper field
         *
         * @private
         * @param {String} pin
         */
        async _storePin(pin) {
            const salt = utils.generate_iv_base64();
            const crypted_pin = await utils.asym_encrypt(
                await vault.get_public_key(),
                pin + salt
            );
            await this._setFieldValue(this.props.fieldPin, crypted_pin);
        }

        /**
         * Get the iterations
         *
         * @returns iterations for the password derivation
         */
        async _getIterations() {
            const record = this.props.record;
            if (!record) return utils.Derive.iterations;
            const iterations = record.data.iterations || utils.Derive.iterations;
            await this._setFieldValue(this.props.fieldIterations, iterations);
            return iterations;
        }

        /**
         * Returns the pin from the class, record data, or generate a new pin if
         * none s currently available
         *
         * @private
         * @returns the pin
         */
        async _getPin() {
            const record = this.props.record;
            if (!record) return null;

            const pin_size = this.context.pin_size || sh_utils.PinSize;

            let pin = record.data[this.props.fieldPin];
            if (pin) {
                // Decrypt the pin and slice him to the configured pin size
                const private_key = await vault.get_private_key();
                const plain = await utils.asym_decrypt(private_key, pin);
                if (!plain) return null;

                pin = plain.slice(0, pin_size);
                return pin;
            }

            // Generate a new pin and store it
            pin = sh_utils.generate_pin(pin_size);
            await this._storePin(pin);
            return pin;
        }

        /**
         * Returns the salt from the class, record data, or generate a new salt if
         * none is currently available
         *
         * @private
         * @returns the salt
         */
        async _getSalt() {
            const record = this.props.record;
            if (!record) return null;

            let salt = record.data[this.props.fieldSalt];
            if (salt) return salt;

            // Generate a new salt and store him
            salt = utils.toBase64(utils.generate_bytes(utils.SaltLength).buffer);
            await this._setFieldValue(this.props.fieldSalt, salt);
            return salt;
        }

        /**
         * Decrypt the encrypted data using the pin, IV and salt
         *
         * @private
         * @param {String} crypted
         * @returns the decrypted secret
         */
        async _decrypt(crypted) {
            if (!utils.supported()) return null;

            if (crypted === false) return false;

            if (!this.props.value) return this.props.value;

            const iv = await this._getIV();
            const pin = await this._getPin();
            const salt = utils.fromBase64(await this._getSalt());
            const iterations = await this._getIterations();

            const key = await utils.derive_key(pin, salt, iterations);
            return await utils.sym_decrypt(key, crypted, iv);
        }

        /**
         * Encrypt the data using the pin, IV and salt
         *
         * @private
         * @param {String} data
         * @returns the encrypted secret
         */
        async _encrypt(data) {
            if (!utils.supported()) return null;

            const iv = await this._getIV();
            const pin = await this._getPin();
            const salt = utils.fromBase64(await this._getSalt());
            const iterations = await this._getIterations();

            const key = await utils.derive_key(pin, salt, iterations);
            return await utils.sym_encrypt(key, data, iv);
        }
    }

    Extended.defaultProps = {
        ...x.defaultProps,
        fieldPin: "pin",
        fieldSalt: "salt",
        fieldIterations: "iterations",
    };
    Extended.props = {
        ...x.props,
        fieldIterations: {type: String, optional: true},
        fieldPin: {type: String, optional: true},
        fieldSalt: {type: String, optional: true},
    };

    return Extended;
};
