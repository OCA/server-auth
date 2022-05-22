// © 2021 Florian Kantelberg - initOS GmbH
// License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

odoo.define("vault.share", function (require) {
    "use strict";

    require("web.dom_ready");

    var utils = require("vault.utils");
    var data = {};

    // Find the elements in the document and check if they have values
    function find_elements() {
        for (const id of ["encrypted", "salt", "iv", "encrypted_file", "filename"])
            if (!data[id]) {
                const element = document.getElementById(id);
                data[id] = element && element.value;
            }
    }

    document.getElementById("pin").onchange = async function () {
        find_elements();

        // Derive the key from the pin
        const key = await utils.derive_key(
            this.value,
            utils.fromBase64(data.salt),
            4000
        );

        const secret = document.getElementById("secret");
        const secret_file = document.getElementById("secret_file");
        if (!secret || !secret_file) return;

        // There is no secret to decrypt
        if (!this.value) {
            secret.setAttribute("class", "alert alert-danger col-12");
            secret_file.setAttribute("class", "alert alert-danger col-12");
            return;
        }

        // Decrypt the data and show the value
        if (data.encrypted) {
            secret.value = await utils.sym_decrypt(key, data.encrypted, data.iv);
            secret.setAttribute("class", "alert alert-success col-12");
        }

        if (data.encrypted_file) {
            const content = await utils.sym_decrypt(key, data.encrypted_file, data.iv);
            const file = new File([atob(content)], data.filename);
            secret_file.text = data.filename;
            secret_file.setAttribute("href", window.URL.createObjectURL(file));
            secret_file.setAttribute("class", "alert alert-success col-12");
        }
    };
});
