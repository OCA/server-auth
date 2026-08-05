# Copyright 2026 ForgeFlow S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Enforce Two-Factor Authentication",
    "summary": "Force users to set up an authenticator app before they can log in.",
    "version": "18.0.1.0.0",
    "author": "ForgeFlow, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/server-auth",
    "category": "Authentication",
    "license": "AGPL-3",
    "depends": ["auth_totp"],
    "data": [
        "security/res_groups.xml",
        "views/templates.xml",
    ],
    "demo": [
        "demo/res_groups_demo.xml",
    ],
    "installable": True,
}
