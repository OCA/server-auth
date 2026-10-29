// © 2021 Florian Kantelberg - initOS GmbH
// License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import {after, beforeEach, describe, expect, test} from "@odoo/hoot";
import {
    getService,
    makeTestApp,
    onRpc,
    patchWithCleanup,
} from "@web/../tests/web_test_helpers";
import utils from "@vault/common/utils.esm";

describe.current.tags("headless");

const SUBTLE_METHODS = [
    "decrypt",
    "deriveKey",
    "digest",
    "encrypt",
    "exportKey",
    "generateKey",
    "importKey",
    "unwrapKey",
    "wrapKey",
];

/**
 * Hoot replaces `window.crypto` with a minimal mock. The vault needs a working
 * SubtleCrypto, so the methods of the mocked object are replaced by the ones of
 * a real SubtleCrypto taken from an iframe. Keys are created in the iframe realm
 * which is why `instanceof CryptoKey` can't be used in the assertions.
 */
beforeEach(() => {
    const iframe = document.createElement("iframe");
    document.body.append(iframe);
    const realSubtle = iframe.contentWindow.crypto.subtle;
    const mockedSubtle = window.crypto.subtle;
    const original = {...mockedSubtle};
    for (const method of SUBTLE_METHODS)
        mockedSubtle[method] = realSubtle[method].bind(realSubtle);
    after(() => {
        for (const method of SUBTLE_METHODS) delete mockedSubtle[method];
        Object.assign(mockedSubtle, original);
        iframe.remove();
    });
});

function expectCryptoKey(key, type) {
    expect(key.constructor.name).toBe("CryptoKey");
    expect(key.type).toBe(type);
}

function expectKeyPair(keys) {
    expectCryptoKey(keys.publicKey, "public");
    expectCryptoKey(keys.privateKey, "private");
}

/**
 * Start the services with a mocked password dialog and mocked key routes
 */
async function makeVaultApp() {
    let storedKeys = {};
    onRpc("/vault/keys/get", () => storedKeys);
    onRpc("/vault/keys/store", async (request) => {
        const {params} = await request.json();
        storedKeys = {...params, uuid: "42"};
        return storedKeys.uuid;
    });
    await makeTestApp();
    patchWithCleanup(getService("vault_utils"), {
        askpass: async () => ({password: "test", keyfile: ""}),
    });
}

describe("utils", () => {
    test("conversion utils", () => {
        let text = "hello world";
        let buf = utils.fromBinary(text);
        expect(buf).toBeInstanceOf(ArrayBuffer);
        expect(utils.toBinary(buf)).toBe(text);
        expect(utils.toBinary(false)).toBe("");

        text = "ImhlbGxvIHdvcmxkIg==";
        buf = utils.fromBase64(text);
        expect(buf).toBeInstanceOf(ArrayBuffer);
        expect(utils.toBase64(buf)).toBe(text);
        expect(utils.toBase64(false)).toBe("");

        expect(utils.capitalize("hello world")).toBe("Hello World");
    });

    test("generation utils", async () => {
        let data = utils.generate_bytes(5);
        expect(data).toBeInstanceOf(Uint8Array);
        expect(data.length).toBe(5);
        data = utils.generate_bytes(10);
        expect(data.length).toBe(10);

        data = utils.generate_iv_base64();
        expect(typeof data).toBe("string");
        expect(data).not.toBe(utils.generate_iv_base64());

        data = await utils.generate_key();
        expectCryptoKey(data, "secret");

        expectKeyPair(await utils.generate_key_pair());

        data = utils.generate_secret(10, "01");
        expect(data.length).toBe(10);
        expect([...data].every((c) => "01".includes(c))).toBe(true);
    });

    test("asymmetric encryption", async () => {
        const text = "hello world";
        const key = await utils.generate_key_pair();

        const crypted = await utils.asym_encrypt(key.publicKey, text);
        expect(typeof crypted).toBe("string");
        expect(await utils.asym_decrypt(key.privateKey, crypted)).toBe(text);
    });

    test("symmetric encryption", async () => {
        const text = "hello world";
        const key = await utils.generate_key();
        const iv = utils.generate_iv_base64();

        const crypted = await utils.sym_encrypt(key, text, iv);
        expect(typeof crypted).toBe("string");
        expect(await utils.sym_decrypt(key, crypted, iv)).toBe(text);
    });

    test("import/export of keys", async () => {
        const key = await utils.generate_key_pair();
        const text = "hello world";

        let exported = await utils.export_public_key(key.publicKey);
        const publicKey = await utils.load_public_key(exported);
        const crypted = await utils.asym_encrypt(publicKey, text);
        expect(await utils.asym_decrypt(key.privateKey, crypted)).toBe(text);

        const iv = utils.generate_bytes(12);
        const salt = utils.generate_bytes(10);
        const wrapper = await utils.derive_key("test", salt, 4000);
        exported = await utils.export_private_key(key.privateKey, wrapper, iv);
        const privateKey = await utils.load_private_key(
            exported,
            wrapper,
            utils.toBase64(iv)
        );
        expect(await utils.asym_decrypt(privateKey, crypted)).toBe(text);

        const master_key = await utils.generate_key();
        exported = await utils.wrap(master_key, key.publicKey);
        const unwrapped = await utils.unwrap(exported, key.privateKey);
        const sym_iv = utils.generate_iv_base64();
        const sym_crypted = await utils.sym_encrypt(master_key, text, sym_iv);
        expect(await utils.sym_decrypt(unwrapped, sym_crypted, sym_iv)).toBe(text);
    });
});

describe("services", () => {
    beforeEach(makeVaultApp);

    test("vault keys are generated and reloaded", async () => {
        const vault = getService("vault");

        await vault._initialize_keys();
        expectKeyPair(vault.keys);

        vault.keys = undefined;
        await vault._import_from_database();
        expectKeyPair(vault.keys);
    });

    test("key generation on first usage", async () => {
        const vault = getService("vault");

        // A first-time user has no keys yet. Accessing the public key
        // must generate them instead of throwing.
        await vault.get_public_key();
        expectKeyPair(vault.keys);
    });

    test("importer/exporter", async () => {
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

        const master_key = await utils.generate_key();
        const imported = await getService("vault_import").import(
            master_key,
            "test.json",
            JSON.stringify(data)
        );
        const exported = await getService("vault_export").export(
            master_key,
            "test.json",
            JSON.stringify(imported)
        );
        expect(exported.type).toBe("encrypted");

        const pass = await utils.derive_key(
            "test",
            utils.fromBase64(exported.salt),
            exported.iterations
        );
        const decrypted = JSON.parse(
            await utils.sym_decrypt(pass, exported.data, exported.iv)
        );
        expect(decrypted).toEqual(data.data);
    });
});
