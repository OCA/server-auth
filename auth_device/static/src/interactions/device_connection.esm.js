import {Interaction} from "@web/public/interaction";
import {registry} from "@web/core/registry";

export class DeviceLogin extends Interaction {
    static selector = ".o_auth_device_login";

    dynamicContent = {
        _root: {"t-on-click.prevent": this.onClick},
    };

    onClick() {
        const modalEl = document.querySelector("#loginDevice");
        if (!modalEl) {
            return;
        }

        window.Modal.getOrCreateInstance(modalEl).show();

        modalEl.addEventListener(
            "shown.bs.modal",
            () => modalEl.querySelector("#device_code_input")?.focus(),
            {once: true}
        );
    }
}

registry.category("public.interactions").add("auth_device.device_login", DeviceLogin);
