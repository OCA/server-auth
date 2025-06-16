# Copyright 2018 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    "name": "Auth Api Key",
    "summary": """
        Authenticate http requests from an API key""",
    "version": "18.0.1.0.1",
    "license": "LGPL-3",
    "author": "ACSONE SA/NV,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/server-auth",
    "development_status": "Production/Stable",
    "depends": ["base_setup"],
    "data": [
        "security/ir.model.access.csv",
        "views/auth_api_key.xml",
        "views/res_config_settings.xml",
    ],
}
