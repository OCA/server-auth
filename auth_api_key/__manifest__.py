# Copyright 2018 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    "name": "Auth Api Key",
    "summary": """
        Authenticate http requests from an API key""",
    "version": "12.0.3.0.0",
    "license": "LGPL-3",
    "author": "ACSONE SA/NV,Odoo Community Association (OCA)",
    "website": "https://acsone.eu/",
    "development_status": "Beta",
    "depends": ["base"],
    "data": ['security/ir.model.access.csv', 'views/auth_api_key.xml'],
    "demo": [],
}
