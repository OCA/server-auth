# Copyright (C) 2024 XCG Consulting <http://odoo.consulting>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "OAuth2 Authentication Autoredirect",
    "version": "16.0.1.0.0",
    "category": "Hidden/Tools",
    "author": "XCG Consulting, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/server-auth",
    "license": "AGPL-3",
    "depends": ["auth_oauth"],
    "data": [
        "views/auth_oauth_provider.xml",
    ],
    "installable": True,
    "auto_install": False,
}
