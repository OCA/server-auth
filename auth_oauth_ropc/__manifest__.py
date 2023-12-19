# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Auth OAuth ROPC",
    "summary": """
        Allow to login with OAuth Resource Owner Password Credentials Grant""",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": "ACSONE SA/NV,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/server-auth",
    "depends": ["base"],
    "data": [
        "security/oauth_ropc_provider.xml",
        "views/oauth_ropc_provider.xml",
    ],
}
