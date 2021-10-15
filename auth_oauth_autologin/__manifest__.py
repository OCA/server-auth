# Copyright 2021 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Auth Oauth Autologin",
    "summary": """
        Automatically redirect to the OAuth provider for login""",
    "version": "13.0.1.0.1",
    "license": "AGPL-3",
    "author": "ACSONE SA/NV,Odoo Community Association (OCA)",
    "maintainers": ["sbidoul"],
    "website": "https://github.com/OCA/server-auth",
    "depends": ["auth_oauth"],
    "data": ["views/auth_oauth_provider.xml"],
    "demo": [],
}
