# Copyright 2019 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
{
    "name": "Two factor authentication via SMS - password reset",
    "version": "10.0.1.0.0",
    "author": "Therp BV,Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "category": "Extra Tools",
    "summary": "Enforces SMS verification for password resets",
    "depends": [
        "auth_signup",
        "auth_sms",
    ],
    "data": [
        "views/templates.xml",
    ],
    "auto_install": True,
}
