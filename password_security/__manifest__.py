# Copyright 2015 LasLabs Inc.
# Copyright 2018 Modoolar <info@modoolar.com>.
# Copyright 2019 initOS GmbH
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
{
    "name": "Password Security",
    "summary": "Allow admin to set password security requirements.",
    "version": "18.0.1.0.0",
    "author": "LasLabs, "
    "Onestein, "
    "Kaushal Prajapati, "
    "Tecnativa, "
    "initOS GmbH, "
    "Omar Nasr, "
    "Odoo Community Association (OCA)",
    "category": "Base",
    "depends": [
        "auth_signup",
        "auth_password_policy_signup",
        "auth_totp",
    ],
    "website": "https://github.com/OCA/server-auth",
    "license": "LGPL-3",
    "data": [
        "views/res_config_settings_views.xml",
        "security/ir.model.access.csv",
        "security/res_users_pass_history.xml",
    ],
    "demo": [
        "demo/res_users.xml",
    ],
    "post_init_hook": "init_config_parameters",
    "installable": True,
}
