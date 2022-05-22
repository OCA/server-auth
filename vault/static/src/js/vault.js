// © 2021 Florian Kantelberg - initOS GmbH
// License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

odoo.define("vault", function (require) {
    "use strict";

    require("web.dom_ready");
    var ajax = require("web.ajax");
    var core = require("web.core");
    var mixins = require("web.mixins");
    var session = require("web.session");
    var utils = require("vault.utils");

    var _t = core._t;

    // Database name on the browser
    const Database = "vault";

    const indexedDB =
        window.indexedDB ||
        window.mozIndexedDB ||
        window.webkitIndexedDB ||
        window.msIndexedDB ||
        window.shimIndexedDB;

    // Expiration time of the vault store entries
    const Expiration = 15 * 60 * 1000;

    /**
     * Ask the user to enter a password using a dialog and put the password together
     *
     * @param {Boolean} confirm
     * @returns password
     */
    async function askpassword(confirm = false) {
        const askpass = await utils.askpass(
            _t("Please enter the password for your private key"),
            {confirm: confirm}
        );

        let password = askpass.password || "";
        if (askpass.keyfile)
            password += await utils.digest(utils.toBinary(askpass.keyfile));

        return session.username + "|" + password;
    }

    // Vault implementation
    var Vault = core.Class.extend(mixins.EventDispatcherMixin, {
        /**
         * Check if the user actually has keys otherwise generate them on init
         *
         * @override
         */
        init: function () {
            mixins.EventDispatcherMixin.init.call(this, arguments);
            var self = this;

            function waitAndCheck() {
                if (odoo.isReady) self._initialize_keys();
                else setTimeout(waitAndCheck, 500);
            }

            setTimeout(waitAndCheck, 500);
        },

        /**
         * RPC call to the backend
         *
         * @param {String} url
         * @param {Object} params
         * @param {Object} options
         * @returns promise
         */
        rpc: function (url, params, options) {
            return ajax.jsonRpc(url, "call", params, _.clone(options || {}));
        },

        /**
         * Generate a new key pair and export to database and object store
         */
        generate_keys: async function () {
            this.keys = await utils.generate_key_pair();
            this.time = new Date();

            if (!(await this._export_to_database()))
                throw Error(_t("Failed to export the keys to the database"));

            await this._export_to_store();
        },

        /**
         * Lazy initialization of the keys which is not fully loading the keys
         * into the javascript but ensures that keys exist in the database to
         * to be loaded
         *
         * @private
         */
        _initialize_keys: async function () {
            // Get the uuid of the currently active keys from the database
            this.uuid = await this._check_database();
            if (this.uuid) {
                // If the object store has the keys it's done
                if (await this._import_from_store()) return;

                // Otherwise an import from the database and export to the object store
                // is needed
                if (await this._import_from_database()) {
                    await this._export_to_store();
                    return true;
                }

                // This should be silent because it would influence the entire workflow
                console.error("Failed to import the keys from the database");
                return false;
            }

            // There are no keys in the database which means we have to generate them
            return await this.generate_keys();
        },

        /**
         * Ensure that the keys are available
         *
         * @private
         */
        _ensure_keys: async function () {
            // Check if the keys expired
            const now = new Date();
            if (now - this.time <= Expiration) return;

            // Keys expired means that we have to get them again
            this.keys = this.time = null;

            // Clear the object store first
            const store = await this._get_object_store();
            store.clear();

            // Import the keys from the database
            if (!(await this._import_from_database()))
                throw Error(_t("Failed to import keys from database"));

            // Store the imported keys in the object store for the next calls
            if (!(await this._export_to_store()))
                throw Error(_t("Failed to export keys to object store"));

            return;
        },

        /**
         * Get the private key and check if the keys expired
         *
         * @returns the private key of the user
         */
        get_private_key: async function () {
            await this._ensure_keys();
            return this.keys.privateKey;
        },

        /**
         * Get the public key and check if the keys expired
         *
         * @returns the public key of the user
         */
        get_public_key: async function () {
            await this._ensure_keys();
            return this.keys.publicKey;
        },

        /**
         * Open the indexed DB and return object store using promise
         *
         * @private
         * @returns a promise
         */
        _get_object_store: function () {
            return new Promise((resolve, reject) => {
                var open = indexedDB.open(Database, 1);
                open.onupgradeneeded = function () {
                    var db = open.result;
                    db.createObjectStore(Database, {keyPath: "id"});
                };

                open.onerror = function (event) {
                    reject(`error opening database ${event.target.errorCode}`);
                };

                open.onsuccess = function () {
                    var db = open.result;
                    var tx = db.transaction(Database, "readwrite");

                    resolve(tx.objectStore(Database));

                    tx.oncomplete = function () {
                        db.close();
                    };
                };
            });
        },

        /**
         * Open the object store and extract the keys using the id
         *
         * @private
         * @param {String} uuid
         * @returns the result from the object store or false
         */
        _get_keys: async function (uuid) {
            var self = this;
            return new Promise((resolve, reject) => {
                self._get_object_store().then((store) => {
                    const request = store.get(uuid);
                    request.onerror = function (event) {
                        reject(`error opening database ${event.target.errorCode}`);
                    };
                    request.onsuccess = function () {
                        resolve(request.result);
                    };
                });
            });
        },

        /**
         * Check if the keys exist in the database
         *
         * @returns the uuid of the currently active keys or false
         */
        _check_database: async function () {
            const params = await this.rpc("/vault/keys/get");
            if (Object.keys(params).length && params.uuid) return params.uuid;
            return false;
        },

        /**
         * Check if the keys exist in the store
         *
         * @private
         * @param {String} uuid
         * @returns if the keys are in the object store
         */
        _check_store: async function (uuid) {
            if (!uuid) return false;

            const result = await this._get_keys(uuid);
            return Boolean(result && result.keys);
        },

        /**
         * Import the keys from the indexed DB
         *
         * @private
         * @returns if the import from the object store succeeded
         */
        _import_from_store: async function () {
            const data = await this._get_keys(this.uuid);
            if (data) {
                this.keys = data.keys;
                this.time = data.time;
                return true;
            }
            return false;
        },

        /**
         * Export the current keys to the indexed DB
         *
         * @private
         * @returns true
         */
        _export_to_store: async function () {
            const keys = {id: this.uuid, keys: this.keys, time: this.time};
            const store = await this._get_object_store();
            store.put(keys);
            return true;
        },

        /**
         * Export the key pairs to the backends
         *
         * @private
         * @returns if the export to the database succeeded
         */
        _export_to_database: async function () {
            // Generate salt for the user key
            this.salt = utils.generate_bytes(utils.SaltLength).buffer;
            this.iterations = 4000;

            // Wrap the private key with the master key of the user
            this.iv = utils.generate_bytes(utils.IVLength);

            // Request the password from the user and derive the user key
            const pass = await utils.derive_key(
                await askpassword(true),
                this.salt,
                this.iterations
            );

            // Export the private key wrapped with the master key
            const private_key = await utils.export_private_key(
                await this.get_private_key(),
                pass,
                this.iv
            );

            // Export the public key
            const public_key = await utils.export_public_key(
                await this.get_public_key()
            );

            const params = {
                public: public_key,
                private: private_key,
                iv: utils.toBase64(this.iv),
                iterations: this.iterations,
                salt: utils.toBase64(this.salt),
            };

            // Export to the server
            const response = await this.rpc("/vault/keys/store", params);
            if (response) {
                this.uuid = response;
                return true;
            }

            console.error("Failed to export keys to database");
            return false;
        },

        /**
         * Import the keys from the backend and decrypt the private key
         *
         * @private
         * @returns if the import succeeded
         */
        _import_from_database: async function () {
            const params = await this.rpc("/vault/keys/get");
            if (Object.keys(params).length) {
                this.salt = utils.fromBase64(params.salt);
                this.iterations = params.iterations;

                // Request the password from the user and derive the user key
                const pass = await utils.derive_key(
                    await askpassword(),
                    this.salt,
                    this.iterations
                );

                this.keys = {
                    publicKey: await utils.load_public_key(params.public),
                    privateKey: await utils.load_private_key(
                        params.private,
                        pass,
                        params.iv
                    ),
                };

                this.time = new Date();
                this.uuid = params.uuid;
                return true;
            }
            return false;
        },

        /**
         * Wrap the master key with the own public key
         *
         * @param {CryptoKey} master_key
         * @returns wrapped master key
         */
        wrap: async function (master_key) {
            return await utils.wrap(master_key, await this.get_public_key());
        },

        /**
         * Wrap the master key with a public key given as string
         *
         * @param {CryptoKey} master_key
         * @param {String} public_key
         * @returns wrapped master key
         */
        wrap_with: async function (master_key, public_key) {
            const pub_key = await utils.load_public_key(public_key);
            return await utils.wrap(master_key, pub_key);
        },

        /**
         * Unwrap the master key with the own private key
         *
         * @param {CryptoKey} master_key
         * @returns unwrapped master key
         */
        unwrap: async function (master_key) {
            return await utils.unwrap(master_key, await this.get_private_key());
        },

        /**
         * Share a wrapped master key by unwrapping with own private key and wrapping with
         * another key
         *
         * @param {String} master_key
         * @param {String} public_key
         * @returns wrapped master key
         */
        share: async function (master_key, public_key) {
            const key = await this.unwrap(master_key);
            return await this.wrap_with(key, public_key);
        },
    });

    return new Vault();
});
