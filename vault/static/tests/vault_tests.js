// © 2021 Florian Kantelberg - initOS GmbH
// License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

/* global QUnit */

odoo.define("vault.tests", function (require) {
    "use strict";

    var utils = require("vault.utils");

    QUnit.module(
        "vault",
        {
            before: function () {
                utils.askpass = async function () {
                    return {
                        password: "test",
                        keyfile: "",
                    };
                };
            },
        },
        function () {
            function is_keypair(keys, assert) {
                assert.equal(keys.publicKey instanceof CryptoKey, true);
                assert.equal(keys.publicKey.type, "public");
                assert.equal(keys.privateKey instanceof CryptoKey, true);
                assert.equal(keys.privateKey.type, "private");
            }

            QUnit.test("vault: Test conversion utils", async function (assert) {
                assert.expect(7);

                let text = "hello world";
                let buf = utils.fromBinary(text);
                assert.equal(true, buf instanceof ArrayBuffer);
                assert.equal(text, utils.toBinary(buf));
                assert.equal("", utils.toBinary(false));

                text = "ImhlbGxvIHdvcmxkIg==";
                buf = utils.fromBase64(text);
                assert.equal(true, buf instanceof ArrayBuffer);
                assert.equal(text, utils.toBase64(buf));
                assert.equal("", utils.toBase64(false));

                assert.equal("Hello World", utils.capitalize("hello world"));
            });

            QUnit.test("vault: Test generation utils", async function (assert) {
                assert.expect(12);

                let data = utils.generate_bytes(5);
                assert.equal(true, data instanceof Uint8Array);
                assert.equal(data.length, 5);
                data = utils.generate_bytes(10);
                assert.equal(data.length, 10);

                data = utils.generate_iv_base64();
                assert.equal(typeof data, "string");
                assert.notEqual(data, utils.generate_iv_base64());

                data = await utils.generate_key();
                assert.equal(true, data instanceof CryptoKey);

                data = await utils.generate_key_pair();
                is_keypair(data, assert);

                data = utils.generate_secret(10, "01");
                assert.equal(data.length, 10);
                let valid = true;
                for (const c of data) if ("01".indexOf(c) < 0) valid = false;
                assert.equal(valid, true);
            });

            QUnit.test("vault: Test asymmetric encryption", async function (assert) {
                assert.expect(2);
                const text = "hello world";
                const key = await utils.generate_key_pair();

                const crypted = await utils.asym_encrypt(key.publicKey, text);
                assert.equal("string", typeof crypted);
                assert.strictEqual(
                    text,
                    await utils.asym_decrypt(key.privateKey, crypted)
                );
            });

            QUnit.test("vault: Test symmetric encryption", async function (assert) {
                assert.expect(2);
                const text = "hello world";
                const key = await utils.generate_key();
                const iv = utils.generate_iv_base64();

                const crypted = await utils.sym_encrypt(key, text, iv);
                assert.equal("string", typeof crypted);
                assert.strictEqual(text, await utils.sym_decrypt(key, crypted, iv));
            });

            QUnit.test("vault: Test import/export", async function (assert) {
                assert.expect(3);

                const key = await utils.generate_key_pair();
                let exported = await utils.export_public_key(key.publicKey);
                let tmp = await utils.load_public_key(exported);
                assert.deepEqual(key.publicKey, tmp);

                const iv = utils.generate_bytes(10);
                const salt = utils.generate_bytes(10);
                const wrapper = await utils.derive_key("test", salt, 4000);
                exported = await utils.export_private_key(key.privateKey, wrapper, iv);
                tmp = await utils.load_private_key(
                    exported,
                    wrapper,
                    utils.toBase64(iv)
                );
                assert.deepEqual(key.privateKey, tmp);

                const master_key = await utils.generate_key();
                exported = await utils.wrap(master_key, key.publicKey);
                tmp = await utils.unwrap(exported, key.privateKey);
                assert.deepEqual(master_key, tmp);
            });

            QUnit.test("vault: Test vault class", async function (assert) {
                assert.expect(12);

                var vault = require("vault");

                await vault._initialize_keys();
                is_keypair(vault.keys, assert);

                vault.keys = undefined;
                await vault._import_from_store();
                is_keypair(vault.keys, assert);

                vault.keys = undefined;
                await vault._import_from_database();
                is_keypair(vault.keys, assert);
            });

            QUnit.test("vault: Importer/exporter", async function (assert) {
                // The exporter won't skip empty keys
                const child = {
                    uuid: "42a",
                    note: "test note child",
                    name: "test child",
                    url: "child.example.org",
                    fields: [],
                    files: [],
                    childs: [],
                };

                const data = {
                    type: "raw",
                    data: [
                        child,
                        {
                            uuid: "42",
                            note: "test note",
                            name: "test name",
                            url: "test.example.org",
                            fields: [
                                {name: "a", value: "Hello World"},
                                {name: "secret", value: "dlrow olleh"},
                            ],
                            files: [],
                            childs: [child, child],
                        },
                        child,
                    ],
                };

                assert.expect(2);

                var Exporter = require("vault.export");
                var Importer = require("vault.import");
                var vault = require("vault");
                await vault._initialize_keys();

                const master_key = await utils.generate_key();
                const importer = new Importer();
                const imported = await importer.import(
                    master_key,
                    "test.json",
                    JSON.stringify(data)
                );

                const exporter = new Exporter();
                const exported = await exporter.export(
                    master_key,
                    "test.json",
                    JSON.stringify(imported)
                );
                assert.equal(exported.type, "encrypted");

                const pass = await utils.derive_key(
                    "test",
                    utils.fromBase64(exported.salt),
                    exported.iterations
                );

                const tmp = JSON.parse(
                    await utils.sym_decrypt(pass, exported.data, exported.iv)
                );
                assert.deepEqual(tmp, data.data);
            });
        }
    );
});
