# Copyright 2021 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Auth Oauth Autologin",
    "summary": """
        Automatically redirect to the OAuth provider for login""",
    "version": "10.0.2.0.0",
    "license": "AGPL-3",
    "author": "ACSONE SA/NV,Odoo Community Association (OCA), The Open Source Company (TOSC)",
    "maintainers": ["sbidoul"],
    "website": "https://github.com/OCA/server-auth",
    "depends": ["auth_oauth"],
    "data": ["views/auth_oauth_provider.xml"],
    "demo": [],
}
