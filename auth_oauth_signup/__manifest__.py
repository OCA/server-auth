# Copyright 2023 Paja SIA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
{
    "name": "OAuth Signup",
    "version": "16.0.1.0.0",
    "website": "https://github.com/OCA/server-auth",
    "depends": [
        "auth_oauth",
    ],
    "author": "Paja SIA, " "Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "summary": "Allow new OAuth2 users to sign up even when global sign up is disabled",
    "category": "Authentication",
    "data": [
        "views/auth_oauth_provider_views.xml",
    ],
}
