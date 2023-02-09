odoo.define("auth_device.connection_device", function () {
    "use strict";

    $(document).ready(function () {
        $("#loginDevice").on("shown.bs.modal", function () {
            $(this).find("#device_code_input").focus();
        });
    });
});
