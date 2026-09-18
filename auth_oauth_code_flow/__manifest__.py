# Copyright 2026 KOBROS-TECH LTD <https://www.kobros-tech.com>
# License: AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

{
    "name": "Authentication OAuth2 Code Flow",
    "version": "18.0.1.0.0",
    "license": "AGPL-3",
    "author": ("KOBROS-TECH LTD, " "Odoo Community Association (OCA)"),
    "maintainers": ["kobros-tech"],
    "website": "https://github.com/OCA/server-auth",
    "summary": """
    Adds Authorization Code Flow support to OAuth2 (e.g., GitHub)
    """,
    "depends": ["auth_oauth", "auth_oidc"],
    "data": [
        "data/auth_oauth_data.xml",
    ],
}
