// © 2021 Florian Kantelberg - initOS GmbH
// License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

odoo.define("vault.inbox", function (require) {
    "use strict";

    require("web.dom_ready");
    var utils = require("vault.utils");

    var data = {};
    var key = false;
    var iv = false;

    const fields = [
        "key",
        "iv",
        "public",
        "encrypted",
        "secret",
        "encrypted_file",
        "filename",
        "secret_file",
    ];

    function toggle_required(element, value) {
        if (value) element.setAttribute("required", "required");
        else element.removeAttribute("required");
    }

    // Encrypt the value and store it in the right input field
    async function encrypt_and_store(value, target) {
        // Find all the possible elements which are needed
        for (const id of fields) if (!data[id]) data[id] = document.getElementById(id);

        // We expect a public key here otherwise we can't procceed
        if (!data.public.value) return;

        const public_key = await utils.load_public_key(data.public.value);

        // Create a new key if not already present
        if (!key) {
            key = await utils.generate_key();
            data.key.value = await utils.wrap(key, public_key);
        }

        // Create a new IV if not already present
        if (!iv) {
            iv = utils.generate_iv_base64();
            data.iv.value = iv;
        }

        // Encrypt the value symmetrically and store it in the field
        const val = await utils.sym_encrypt(key, value, iv);
        data[target].value = val;
        return Boolean(val);
    }

    document.getElementById("secret").onchange = async function () {
        if (!this.value) return;

        const required = await encrypt_and_store(this.value, "encrypted");
        toggle_required(data.secret, required);
        toggle_required(data.secret_file, !required);
    };

    document.getElementById("secret_file").onchange = async function () {
        if (!this.files.length) return;

        const file = this.files[0];
        const value = await file.text();
        if (!value) return;

        const required = await encrypt_and_store(value, "encrypted_file");
        toggle_required(data.secret, !required);
        toggle_required(data.secret_file, required);
        data.filename.value = file.name;
    };
});
