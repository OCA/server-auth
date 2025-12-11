import {Component, onMounted, useRef, useState} from "@odoo/owl";
import {Dialog} from "@web/core/dialog/dialog";
import {_t} from "@web/core/l10n/translation";
import {registry} from "@web/core/registry";
import utils from "./utils.esm";

export class AskPassDialog extends Component {
    static template = "vault.AskPassDialog";
    static components = {Dialog};

    setup() {
        this.state = useState({
            password: "",
            confirm: "",
            error: "",
        });
        this.keyfileInput = useRef("keyfileInput");
    }

    async onConfirm() {
        const {confirm} = this.props;
        const password = this.state.password;
        let keyfileContent = null;
        const input = this.keyfileInput.el;
        if (input && input.files && input.files[0]) {
            const file = input.files[0];
            const text = await file.text();
            keyfileContent = utils.fromBinary(text);
        }
        if (!password && !keyfileContent) {
            this.state.error = _t("Missing password");
            return;
        }
        if (confirm && password && this.state.confirm !== password) {
            this.state.error = _t("The passwords aren't matching");
            return;
        }
        this.props.onResolve({
            password,
            keyfile: keyfileContent,
        });
        this.props.close();
    }

    onCancel() {
        this.props.onReject(_t("Cancelled"));
        this.props.close();
    }
}

export class GeneratePassDialog extends Component {
    static template = "vault.GeneratePassDialog";
    static components = {Dialog};

    setup() {
        this.state = useState({
            length: 15,
            big: true,
            small: true,
            digits: true,
            special: false,
            password: "",
            error: "",
        });

        onMounted(() => this.generate());
    }

    generate() {
        let characters = "";
        if (this.state.big) characters += "ABCDEFGHIJKLMNOPQRSTUVWXYZ";
        if (this.state.small) characters += "abcdefghijklmnopqrstuvwxyz";
        if (this.state.digits) characters += "0123456789";
        if (this.state.special) characters += "!?$%&/()[]{}|<>,;.:-_#+*\\";

        if (!characters) {
            this.state.password = "";
            this.state.error = _t("Select at least one character set");
            return;
        }

        this.state.error = "";
        this.state.password = utils.generate_secret(this.state.length, characters);
    }

    onOptionsChange() {
        this.generate();
    }

    onCancel() {
        this.props.onReject(_t("Cancelled"));
        this.props.close();
    }

    onConfirm() {
        if (!this.state.password) {
            this.state.error = _t("Missing password");
            return;
        }
        this.props.onResolve(this.state.password);
        this.props.close();
    }
}

export const vaultUtilsService = {
    dependencies: ["dialog"],

    start(env, {dialog}) {
        function askpass(title, options = {}) {
            const props = {
                title,
                confirm: Boolean(options.confirm),
            };
            return new Promise((resolve, reject) => {
                dialog.add(AskPassDialog, {
                    ...props,
                    onResolve: resolve,
                    onReject: reject,
                });
            });
        }

        function generate_pass(title, options = {}) {
            const props = {title, ...options};
            return new Promise((resolve, reject) => {
                dialog.add(GeneratePassDialog, {
                    ...props,
                    onResolve: resolve,
                    onReject: reject,
                });
            });
        }

        return {
            ...utils,
            askpass,
            generate_pass,
        };
    },
};

registry.category("services").add("vault_utils", vaultUtilsService);
