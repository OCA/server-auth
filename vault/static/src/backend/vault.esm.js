// © 2021-2024 Florian Kantelberg - initOS GmbH
// License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import {_t} from "@web/core/l10n/translation";
import {registry} from "@web/core/registry";
import {rpc} from "@web/core/network/rpc";
import {session} from "@web/session";

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

const vaultService = {
    dependencies: ["vault_utils"],
    start(env, {vault_utils}) {
        /**
         * Ask the user to enter a password using a dialog and put the password together
         *
         * @param {Boolean} confirm
         * @returns password
         */
        async function askpassword(confirm = false) {
            const askpass = await vault_utils.askpass(
                _t("Please enter the password for your private key"),
                {confirm}
            );

            let password = askpass.password || "";
            if (askpass.keyfile) {
                password += await vault_utils.digest(
                    vault_utils.toBinary(askpass.keyfile)
                );
            }
            return password;
        }

        class Vault {
            /**
             * Check if the user actually has keys otherwise generate them on init
             *
             * @override
             */
            constructor() {
                const self = this;

                function waitAndCheck() {
                    if (!vault_utils.supported()) return null;

                    if (odoo.isReady) self._initialize_keys();
                    else setTimeout(waitAndCheck, 500);
                }

                setTimeout(waitAndCheck, 500);
            }

            /**
             * Generate a new key pair and export to database and object store
             */
            async generate_keys() {
                this.keys = await vault_utils.generate_key_pair();
                this.time = new Date();

                if (!(await this._export_to_database()))
                    throw Error(_t("Failed to export the keys to the database"));

                await this._export_to_store();
            }

            /**
             * Check if export to database is required due to key migration
             *
             * @private
             * @param {String} password
             */
            async _check_key_migration(password = null) {
                if (!this.version) await this._export_to_database(password);
                if (this.iterations < vault_utils.Derive.iterations)
                    await this._export_to_database(password);
            }

            /**
             * Lazy initialization of the keys which is not fully loading the keys
             * into the javascript but ensures that keys exist in the database to
             * to be loaded
             *
             * @private
             */
            async _initialize_keys() {
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
            }

            /**
             * Ensure that the keys are available
             *
             * @private
             */
            async _ensure_keys() {
                // If the object store has the keys it's done
                if (this.uuid && !this.time) await this._import_from_store();

                // Check if the keys expired
                const now = new Date();
                if (this.time && now - this.time <= Expiration) return;

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
            }

            /**
             * Get the private key and check if the keys expired
             *
             * @returns the private key of the user
             */
            async get_private_key() {
                await this._ensure_keys();
                return this.keys.privateKey;
            }

            /**
             * Get the public key and check if the keys expired
             *
             * @returns the public key of the user
             */
            async get_public_key() {
                await this._ensure_keys();
                return this.keys.publicKey;
            }

            /**
             * Open the indexed DB and return object store using promise
             *
             * @private
             * @returns a promise
             */
            _get_object_store() {
                return new Promise((resolve, reject) => {
                    const open = indexedDB.open(Database, 1);
                    open.onupgradeneeded = function () {
                        const db = open.result;
                        db.createObjectStore(Database, {keyPath: "id"});
                    };

                    open.onerror = function (event) {
                        reject(`error opening database ${event.target.errorCode}`);
                    };

                    open.onsuccess = function () {
                        const db = open.result;
                        const tx = db.transaction(Database, "readwrite");

                        resolve(tx.objectStore(Database));

                        tx.oncomplete = function () {
                            db.close();
                        };
                    };
                });
            }

            /**
             * Open the object store and extract the keys using the id
             *
             * @private
             * @param {String} uuid
             * @returns the result from the object store or false
             */
            async _get_keys(uuid) {
                const self = this;
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
            }

            /**
             * Check if the keys exist in the database
             *
             * @returns the uuid of the currently active keys or false
             */
            async _check_database() {
                const params = await rpc("/vault/keys/get");
                if (Object.keys(params).length && params.uuid) return params.uuid;
                return false;
            }

            /**
             * Check if the keys exist in the store
             *
             * @private
             * @param {String} uuid
             * @returns if the keys are in the object store
             */
            async _check_store(uuid) {
                if (!uuid) return false;

                const result = await this._get_keys(uuid);
                return Boolean(result && result.keys);
            }

            /**
             * Import the keys from the indexed DB
             *
             * @private
             * @returns if the import from the object store succeeded
             */
            async _import_from_store() {
                const data = await this._get_keys(this.uuid);
                if (data) {
                    this.keys = data.keys;
                    this.time = data.time;
                    return true;
                }
                return false;
            }

            /**
             * Export the current keys to the indexed DB
             *
             * @private
             * @returns true
             */
            async _export_to_store() {
                const keys = {id: this.uuid, keys: this.keys, time: this.time};
                const store = await this._get_object_store();
                store.put(keys);
                return true;
            }

            /**
             * Export the key pairs to the backends
             *
             * @private
             * @param {String} password
             * @returns if the export to the database succeeded
             */
            async _export_to_database(password = null) {
                // Generate salt for the user key
                this.salt = vault_utils.generate_bytes(vault_utils.SaltLength).buffer;
                this.iterations = vault_utils.Derive.iterations;
                this.version = 1;

                // Wrap the private key with the master key of the user
                this.iv = vault_utils.generate_bytes(vault_utils.IVLength);

                // Request the password from the user and derive the user key
                const pass = await vault_utils.derive_key(
                    password || (await askpassword(true)),
                    this.salt,
                    this.iterations
                );

                // Export the private key wrapped with the master key
                const private_key = await vault_utils.export_private_key(
                    await this.get_private_key(),
                    pass,
                    this.iv
                );

                // Export the public key
                const public_key = await vault_utils.export_public_key(
                    await this.get_public_key()
                );

                const params = {
                    public: public_key,
                    private: private_key,
                    iv: vault_utils.toBase64(this.iv),
                    iterations: this.iterations,
                    salt: vault_utils.toBase64(this.salt),
                    version: this.version,
                };

                // Export to the server
                const response = await rpc("/vault/keys/store", params);
                if (response) {
                    this.uuid = response;
                    return true;
                }

                console.error("Failed to export keys to database");
                return false;
            }

            /**
             * Import the keys from the backend and decrypt the private key
             *
             * @private
             * @returns if the import succeeded
             */
            async _import_from_database() {
                const params = await rpc("/vault/keys/get");
                if (Object.keys(params).length) {
                    this.salt = vault_utils.fromBase64(params.salt);
                    this.iterations = params.iterations;
                    this.version = params.version || 0;

                    // Request the password from the user and derive the user key
                    const raw_password = await askpassword(false);
                    let password = raw_password;

                    // Compatibility
                    if (!this.version) password = session.username + "|" + password;

                    const pass = await vault_utils.derive_key(
                        password,
                        this.salt,
                        this.iterations
                    );

                    this.keys = {
                        publicKey: await vault_utils.load_public_key(params.public),
                        privateKey: await vault_utils.load_private_key(
                            params.private,
                            pass,
                            params.iv
                        ),
                    };

                    this.time = new Date();
                    this.uuid = params.uuid;

                    this._check_key_migration(raw_password);
                    return true;
                }
                return false;
            }

            /**
             * Wrap the master key with the own public key
             *
             * @param {CryptoKey} master_key
             * @returns wrapped master key
             */
            async wrap(master_key) {
                return await vault_utils.wrap(master_key, await this.get_public_key());
            }

            /**
             * Wrap the master key with a public key given as string
             *
             * @param {CryptoKey} master_key
             * @param {String} public_key
             * @returns wrapped master key
             */
            async wrap_with(master_key, public_key) {
                const pub_key = await vault_utils.load_public_key(public_key);
                return await vault_utils.wrap(master_key, pub_key);
            }

            /**
             * Unwrap the master key with the own private key
             *
             * @param {CryptoKey} master_key
             * @returns unwrapped master key
             */
            async unwrap(master_key) {
                return await vault_utils.unwrap(
                    master_key,
                    await this.get_private_key()
                );
            }

            /**
             * Share a wrapped master key by unwrapping with own private key and wrapping with
             * another key
             *
             * @param {String} master_key
             * @param {String} public_key
             * @returns wrapped master key
             */
            async share(master_key, public_key) {
                const key = await this.unwrap(master_key);
                return await this.wrap_with(key, public_key);
            }
        }
        return new Vault();
    },
};

registry.category("services").add("vault", vaultService);
