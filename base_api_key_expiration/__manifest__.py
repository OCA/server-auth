# Copyright 2026 Camptocamp SA
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
{
    "name": "API Keys Expiration",
    "summary": "Backport of the expiration date of the API keys (Odoo 18.0)",
    "version": "17.0.1.0.0",
    "author": "Camptocamp,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/server-auth",
    "license": "LGPL-3",
    "category": "Tools",
    "development_status": "Beta",
    "depends": [
        "base",
    ],
    "data": [
        "data/res_groups.xml",
        "views/res_groups.xml",
        "views/res_users.xml",
    ],
}
