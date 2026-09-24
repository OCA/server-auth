# Copyright 2026 Camptocamp SA
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
{
    "name": "2FA Trusted Device Age",
    "summary": "Backport of the trusted device age setting (Odoo 19.0)",
    "version": "17.0.1.0.0",
    "author": "Camptocamp,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/server-auth",
    "license": "LGPL-3",
    "category": "Tools",
    "development_status": "Beta",
    "depends": [
        "auth_totp",
        "base_api_key_expiration",
    ],
    "post_init_hook": "post_init_hook",
}
