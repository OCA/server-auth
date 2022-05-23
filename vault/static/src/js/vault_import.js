// © 2021 Florian Kantelberg - initOS GmbH
// License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

/* global kdbxweb */

odoo.define("vault.import", function(require) {
    "use strict";

    var core = require("web.core");
    var framework = require("web.framework");
    var mixins = require("web.mixins");
    var utils = require("vault.utils");

    var _t = core._t;

    async function encrypted_field(master_key, name, value) {
        if (!value) return null;

        const iv = utils.generate_iv_base64();
        return {
            name: name,
            iv: iv,
            value: await utils.sym_encrypt(master_key, value, iv),
        };
    }

    // This class handles the import from different formats by returning
    // an importable JSON formatted data which will be handled by the python
    // backend.
    //
    // JSON format description:
    //
    // Entries are represented as objects with the following attributes
    //  `name`, `uuid`, `url`, `note`
    //     Specific fields of the entry. `uuid` is used for updating existing records
    //  `childs`
    //     Child entries
    //  `fields`, `files`
    //     List of encypted fields/files with `name`, `iv`, and `value`
    //
    var VaultImporter = core.Class.extend(mixins.EventDispatcherMixin, {
        /**
         * Encrypt a field of the above format properly for the backend to store.
         * The changes are done inplace.
         *
         * @private
         * @param {CryptoKey} master_key
         * @param {Object} node
         */
        _import_json_entry: async function(master_key, node) {
            for (const field of node.fields || []) {
                field.iv = utils.generate_iv_base64();
                field.value = await utils.sym_encrypt(
                    master_key,
                    field.value,
                    field.iv
                );
            }

            for (const file of node.files || []) {
                file.iv = utils.generate_iv_base64();
                file.value = await utils.sym_encrypt(master_key, file.value, file.iv);
            }

            for (const entry of node.childs || [])
                await this._import_json_entry(master_key, entry);
        },

        /**
         * Encrypt the data from the JSON import. This will add `iv` to fields and files
         * and encrypt the `value`
         *
         * @private
         * @param {CryptoKey} master_key
         * @param {String} data
         * @returns the encrypted entry for the database
         */
        _import_json_data: async function(master_key, data) {
            for (const node of data) await this._import_json_entry(master_key, node);
            return data;
        },

        /**
         * Load from an encrypted JSON file. Encrypt the data with similar format as
         * described above. This will add `iv` to fields and files and encrypt the `value`
         *
         * @private
         * @param {CryptoKey} master_key
         * @param {Object} content
         * @returns the encrypted entry for the database
         */
        _import_encrypted_json: async function(master_key, content) {
            const askpass = await utils.askpass(
                _t("Please enter the password for the database")
            );
            let password = askpass.password || "";
            if (askpass.keyfile)
                password += await utils.digest(utils.toBinary(askpass.keyfile));

            const key = await utils.derive_key(
                password,
                utils.fromBase64(content.salt),
                content.iterations
            );
            const result = await utils.sym_decrypt(key, content.data, content.iv);
            return await this._import_json_data(master_key, JSON.parse(result));
        },

        /**
         * Import using JSON format. The database is stored in the `data` field of the JSON
         * type and is either a JSON object or an encrypted JSON object. For the encryption
         * the needed encryption parameter `iv`, `salt` and `iterations` are stored in the
         * file. This will add `iv` to fields and files and encrypt the `value`
         *
         * @private
         * @param {CryptoKey} master_key
         * @param {String} data
         * @returns the encrypted entry for the database
         */
        _import_json: async function(master_key, data) {
            // Unwrap the master key and encrypt the entries
            const result = JSON.parse(data);
            switch (result.type) {
                case "encrypted":
                    return await this._import_encrypted_json(master_key, result);
                case "raw":
                    return await this._import_json_data(master_key, result.data);
            }

            throw Error(_t("Unsupported file to import"));
        },

        /**
         * Encrypt an entry from the kdbx file properly for the backend to store
         *
         * @private
         * @param {CryptoKey} master_key
         * @param {Object} entry
         * @returns the encrypted entry for the database
         */
        _import_kdbx_entry: async function(master_key, entry) {
            let pass = entry.fields.Password;
            if (pass) pass = pass.getText();

            const res = {
                uuid: entry.uuid && entry.uuid.id,
                note: entry.fields.Notes,
                name: entry.fields.Title,
                url: entry.fields.URL,
                fields: [
                    await encrypted_field(
                        master_key,
                        "Username",
                        entry.fields.UserName
                    ),
                    await encrypted_field(master_key, "Password", pass),
                ],
                files: [],
            };

            for (const name in entry.binaries)
                res.files.push(
                    await encrypted_field(
                        master_key,
                        name,
                        utils.toBase64(entry.binaries[name].value)
                    )
                );

            return res;
        },

        /**
         * Handle a kdbx group entry by creating an sub-entry and calling the right functions
         * on the childs
         *
         * @private
         * @param {CryptoKey} master_key
         * @param {Object} group
         * @returns the encrypted entry for the database
         */
        _import_kdbx_group: async function(master_key, group) {
            const res = {
                uuid: group.uuid && group.uuid.id,
                name: group.name,
                note: group.notes,
                childs: [],
            };

            for (const sub_group of group.groups || [])
                res.childs.push(await this._import_kdbx_group(master_key, sub_group));

            for (const entry of group.entries || [])
                res.childs.push(await this._import_kdbx_entry(master_key, entry));

            return res;
        },

        /**
         * Load a kdbx file, encrypt the data, and return in the described JSON format
         *
         * @private
         * @param {CryptoKey} master_key
         * @param {String} data
         * @returns the encrypted data for the backend
         */
        _import_kdbx: async function(master_key, data) {
            // Get the credentials of the keepass database
            const askpass = await utils.askpass(
                _t("Please enter the password for the keepass database")
            );

            // TODO: challenge-response
            const credentials = new kdbxweb.Credentials(
                (askpass.password &&
                    kdbxweb.ProtectedValue.fromString(askpass.password)) ||
                    null,
                askpass.keyfile || null
            );

            // Convert the data to an ArrayBuffer
            const buffer = utils.fromBinary(data);

            // Decrypt the database
            const db = await kdbxweb.Kdbx.load(buffer, credentials);

            try {
                // Unwrap the master key, format, and encrypt the database
                framework.blockUI();
                const result = [];
                for (const group of db.groups)
                    result.push(await this._import_kdbx_group(master_key, group));
                return result;
            } finally {
                framework.unblockUI();
            }
        },

        /**
         * The main import functions which checks the file ending and calls the right function
         * to handle the rest of the import
         *
         * @private
         * @param {CryptoKey} master_key
         * @param {String} filename
         * @param {String} content
         * @returns the data importable by the backend or false on error
         */
        import: async function(master_key, filename, content) {
            if (!utils.supported()) return false;

            if (filename.endsWith(".json"))
                return await this._import_json(master_key, content);
            else if (filename.endsWith(".kdbx"))
                return await this._import_kdbx(master_key, content);
            return false;
        },
    });

    return VaultImporter;
});
