// © 2021-2024 Florian Kantelberg - initOS GmbH
// License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
const CryptoAPI = window.crypto?.subtle;

// Some basic constants used for the entire vaults
const Hash = "SHA-512";
const HashLength = 10;
const IVLength = 12;
const SaltLength = 32;

const Asymmetric = {
    name: "RSA-OAEP",
    modulusLength: 4096,
    publicExponent: new Uint8Array([1, 0, 1]),
    hash: Hash,
};
const Derive = {
    name: "PBKDF2",
    iterations: 600001,
};
const Symmetric = {
    name: "AES-GCM",
    length: 256,
};

/**
 * Checks if the CryptoAPI is available and the vault feature supported
 *
 * @returns if vault is supported
 */
function supported() {
    return Boolean(CryptoAPI);
}

/**
 * Converts an ArrayBuffer to an ASCII string
 *
 * @param {ArrayBuffer} buffer
 * @returns the data converted to a string
 */
function toBinary(buffer) {
    if (!buffer) return "";
    const chars = Array.from(new Uint8Array(buffer)).map((b) => String.fromCharCode(b));
    return chars.join("");
}

/**
 * Converts an ASCII string to an ArrayBuffer
 *
 * @param {String} binary
 * @returns the data converted to an ArrayBuffer
 */
function fromBinary(binary) {
    const len = binary.length;
    const bytes = new Uint8Array(len);
    for (let i = 0; i < len; i++) bytes[i] = binary.charCodeAt(i);
    return bytes.buffer;
}

/**
 * Converts an ArrayBuffer to a Base64 encoded string
 *
 * @param {ArrayBuffer} buffer
 * @returns Base64 string
 */
function toBase64(buffer) {
    if (!buffer) return "";
    const chars = Array.from(new Uint8Array(buffer)).map((b) => String.fromCharCode(b));
    return btoa(chars.join(""));
}

/**
 * Converts an Base64 encoded string to an ArrayBuffer
 *
 * @param {String} base64
 * @returns the data converted to an ArrayBuffer
 */
function fromBase64(base64) {
    if (!base64) {
        const bytes = new Uint8Array(0);
        return bytes.buffer;
    }
    const binary_string = atob(base64);
    const len = binary_string.length;
    const bytes = new Uint8Array(len);
    for (let i = 0; i < len; i++) bytes[i] = binary_string.charCodeAt(i);
    return bytes.buffer;
}

/**
 * Generate random bytes used for salts or IVs
 *
 * @param {int} length
 * @returns an array with length random bytes
 */
function generate_bytes(length) {
    const buf = new Uint8Array(length);
    window.crypto.getRandomValues(buf);
    return buf;
}

/**
 * Generate random bytes used for salts or IVs encoded as base64
 *
 * @returns base64 string
 */
function generate_iv_base64() {
    return toBase64(generate_bytes(IVLength));
}

/**
 * Generate a random secret with specific characters
 *
 * @param {int} length
 * @param {String} characters
 * @returns base64 string
 */
function generate_secret(length, characters) {
    let result = "";
    const len = characters.length;
    for (const k of generate_bytes(length)) {
        result += characters[Math.floor((len * k) / 256)];
    }
    return result;
}

/**
 * Generate a symmetric key for encrypting and decrypting
 *
 * @returns symmetric key
 */
async function generate_key() {
    return await CryptoAPI.generateKey(Symmetric, true, ["encrypt", "decrypt"]);
}

/**
 * Generate an asymmetric key pair for encrypting, decrypting, wrapping and unwrapping
 *
 * @returns asymmetric key
 */
async function generate_key_pair() {
    return await CryptoAPI.generateKey(Asymmetric, true, [
        "wrapKey",
        "unwrapKey",
        "decrypt",
        "encrypt",
    ]);
}

/**
 * Generate a hash of the given data
 *
 * @param {String} data
 * @returns base64 encoded hash of the data
 */
async function digest(data) {
    const encoder = new TextEncoder();
    return toBase64(await CryptoAPI.digest(Hash, encoder.encode(data)));
}

/**
 * Derive a key using the given data, salt and iterations using PBKDF2
 *
 * @param {String} data
 * @param {String} salt
 * @param {int} iterations
 * @returns the derived key
 */
async function derive_key(data, salt, iterations) {
    const enc = new TextEncoder();
    const material = await CryptoAPI.importKey(
        "raw",
        enc.encode(data),
        Derive.name,
        false,
        ["deriveBits", "deriveKey"]
    );

    return await CryptoAPI.deriveKey(
        {
            name: Derive.name,
            salt: salt,
            iterations: iterations,
            hash: Hash,
        },
        material,
        Symmetric,
        false,
        ["wrapKey", "unwrapKey", "encrypt", "decrypt"]
    );
}

/**
 * Encrypt the data using a public key
 *
 * @param {CryptoKey} public_key
 * @param {String} data
 * @returns the encrypted data
 */
async function asym_encrypt(public_key, data) {
    if (!data) return data;
    const enc = new TextEncoder();
    return toBase64(
        await CryptoAPI.encrypt({name: Asymmetric.name}, public_key, enc.encode(data))
    );
}

/**
 * Decrypt the data using the own private key
 *
 * @param {CryptoKey} private_key
 * @param {String} crypted
 * @returns the decrypted data
 */
async function asym_decrypt(private_key, crypted) {
    if (!crypted) return crypted;
    const dec = new TextDecoder();
    return dec.decode(
        await CryptoAPI.decrypt(
            {name: Asymmetric.name},
            private_key,
            fromBase64(crypted)
        )
    );
}

/**
 * Symmetrically encrypt the data using a master key
 *
 * @param {CryptoKey} key
 * @param {String} data
 * @param {String} iv
 * @returns the encrypted data
 */
async function sym_encrypt(key, data, iv) {
    if (!data) return data;
    const hash = await digest(data);
    const enc = new TextEncoder();
    return toBase64(
        await CryptoAPI.encrypt(
            {name: Symmetric.name, iv: fromBase64(iv), tagLength: 128},
            key,
            enc.encode(hash.slice(0, HashLength) + data)
        )
    );
}

/**
 * Symmetrically decrypt the data using a master key
 *
 * @param {CryptoKey} key
 * @param {String} crypted
 * @param {String} iv
 * @returns the decrypted data
 */
async function sym_decrypt(key, crypted, iv) {
    if (!crypted) return crypted;
    try {
        const dec = new TextDecoder();
        const message = dec.decode(
            await CryptoAPI.decrypt(
                {name: Symmetric.name, iv: fromBase64(iv), tagLength: 128},
                key,
                fromBase64(crypted)
            )
        );
        const data = message.slice(HashLength);
        const hash = await digest(data);
        // Compare the hash and return if integer
        if (hash.slice(0, HashLength) === message.slice(0, HashLength)) return data;

        console.error("Invalid data hash");
        // Wrong hash
        return null;
    } catch (err) {
        console.error(err);
        return null;
    }
}

/**
 * Load a public key
 *
 * @param {String} public_key
 * @returns the public key as CryptoKey
 */
async function load_public_key(public_key) {
    return await CryptoAPI.importKey("spki", fromBase64(public_key), Asymmetric, true, [
        "wrapKey",
        "encrypt",
    ]);
}

/**
 * Load a private key
 *
 * @param {String} private_key
 * @param {CryptoKey} key
 * @param {String} iv
 * @returns the private key as CryptoKey
 */
async function load_private_key(private_key, key, iv) {
    return await CryptoAPI.unwrapKey(
        "pkcs8",
        fromBase64(private_key),
        key,
        {name: Symmetric.name, iv: fromBase64(iv), tagLength: 128},
        Asymmetric,
        true,
        ["unwrapKey", "decrypt"]
    );
}

/**
 * Export a public key in spki format
 *
 * @param {CryptoKey} public_key
 * @returns the public key as string
 */
async function export_public_key(public_key) {
    return toBase64(await CryptoAPI.exportKey("spki", public_key));
}

/**
 * Export a private key in pkcs8 format
 *
 * @param {String} private_key
 * @param {CryptoKey} key
 * @param {String} iv
 * @returns the public key as CryptoKey
 */
async function export_private_key(private_key, key, iv) {
    return toBase64(
        await CryptoAPI.wrapKey("pkcs8", private_key, key, {
            name: Symmetric.name,
            iv: iv,
            tagLength: 128,
        })
    );
}

/**
 * Wrap the master key with the own public key
 *
 * @param {CryptoKey} key
 * @param {CryptoKey} public_key
 * @returns wrapped master key
 */
async function wrap(key, public_key) {
    return toBase64(await CryptoAPI.wrapKey("raw", key, public_key, Asymmetric));
}

/**
 * Unwrap the master key with the own private key
 *
 * @param {CryptoKey} key
 * @param {CryptoKey} private_key
 * @returns unwrapped master key
 */
async function unwrap(key, private_key) {
    return await CryptoAPI.unwrapKey(
        "raw",
        fromBase64(key),
        private_key,
        Asymmetric,
        Symmetric,
        true,
        ["encrypt", "decrypt"]
    );
}

/**
 * Capitalize each word of the string
 *
 * @param {String} s
 * @returns capitalized string
 */
function capitalize(s) {
    return s.toLowerCase().replace(/\b\w/g, (c) => c.toUpperCase());
}

export default {
    Asymmetric,
    Derive,
    Hash,
    HashLength,
    IVLength,
    SaltLength,
    Symmetric,
    // Crypto
    supported,
    digest,
    derive_key,
    generate_bytes,
    generate_iv_base64,
    generate_secret,
    generate_key,
    generate_key_pair,
    asym_encrypt,
    asym_decrypt,
    sym_encrypt,
    sym_decrypt,
    load_public_key,
    load_private_key,
    export_public_key,
    export_private_key,
    wrap,
    unwrap,
    // Utils
    capitalize,
    toBase64,
    fromBase64,
    toBinary,
    fromBinary,
};
