// © 2021-2024 Florian Kantelberg - initOS GmbH
// License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import utils from "@vault/common/utils.esm";

const data = {};

// Find the elements in the document and check if they have values
function find_elements() {
    for (const id of [
        "encrypted",
        "salt",
        "iv",
        "encrypted_file",
        "filename",
        "iterations",
    ])
        if (!data[id]) {
            const element = document.getElementById(id);
            data[id] = element && element.value;
        }
}

function toggle_alert(element, successful) {
    if (element) {
        element.classList.add(successful ? "alert-success" : "alert-danger");
        element.classList.remove(successful ? "alert-danger" : "alert-success");
    }
}

function show(selector) {
    const element = document.querySelector(selector);
    if (element) element.classList.remove("o_hidden");
}

function hide(selector) {
    const element = document.querySelector(selector);
    if (element) element.classList.add("o_hidden");
}

document.getElementById("pin").onchange = async function () {
    if (!utils.supported()) return;

    find_elements();

    // Derive the key from the pin
    const key = await utils.derive_key(
        this.value,
        utils.fromBase64(data.salt),
        data.iterations
    );

    hide("#secret_group");
    hide("#file_group");

    const pin = document.getElementById("pin");
    const secret = document.getElementById("secret");
    const secret_file = document.getElementById("secret_file");
    if (!secret && !secret_file) return;

    // There is no secret to decrypt
    if (!this.value) {
        toggle_alert(pin, false);
        return;
    }

    // Decrypt the data and show the value
    if (data.encrypted) {
        secret.value = await utils.sym_decrypt(key, data.encrypted, data.iv);
        toggle_alert(pin, secret.value);
        show("#secret_group");
    }

    if (data.encrypted_file) {
        const content = atob(
            await utils.sym_decrypt(key, data.encrypted_file, data.iv)
        );
        const buffer = new ArrayBuffer(content.length);
        const arr = new Uint8Array(buffer);
        for (let i = 0; i < content.length; i++) arr[i] = content.charCodeAt(i);
        const file = new Blob([arr]);

        secret_file.text = data.filename;
        secret_file.setAttribute("href", window.URL.createObjectURL(file));
        secret_file.setAttribute("download", data.filename);
        toggle_alert(pin, content);
        show("#file_group");
    }
};
