# Copyright 2026 Trobz
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Auth Api Key Native Generate",
    "summary": """
        Endpoint to generate a native Odoo API key from user credentials""",
    "version": "19.0.1.0.0",
    "license": "AGPL-3",
    "author": "Trobz,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/server-auth",
    "development_status": "Beta",
    "depends": ["base_setup"],
    "data": [
        "views/res_config_settings.xml",
    ],
}
