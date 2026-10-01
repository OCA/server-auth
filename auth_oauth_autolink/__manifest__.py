# Copyright 2026 Nimarosa
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "OAuth Autolink by Verified Email",
    "summary": "Link an OAuth login to the existing user whose login is the "
    "provider-verified email address",
    "version": "18.0.1.0.0",
    "category": "Authentication",
    "website": "https://github.com/OCA/server-auth",
    "author": "Nimarosa, Odoo Community Association (OCA)",
    "maintainers": ["nimarosa"],
    "license": "AGPL-3",
    "development_status": "Beta",
    "depends": [
        "auth_oauth",
        "mail",
    ],
    "data": [
        "views/auth_oauth_views.xml",
    ],
    "installable": True,
}
