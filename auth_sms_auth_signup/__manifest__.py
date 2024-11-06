# Copyright 2019-2025 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
{
    "name": "Two factor authentication via SMS - password reset",
    "version": "16.0.1.0.0",
    "author": "Therp BV,Odoo Community Association (OCA)",
    "maintainers": ["NL66278"],
    "license": "AGPL-3",
    "category": "Tools",
    "website": "https://github.com/OCA/server-auth",
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
