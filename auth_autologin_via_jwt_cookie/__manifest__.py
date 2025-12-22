# Copyright 2025 Kencove (https://www.kencove.com/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Auth Autologin via JWT Cookie",
    "summary": "Auto-authenticate users using a shared JWT cookie",
    "version": "16.0.1.0.0",
    "category": "Authentication",
    "author": "Kencove,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/server-auth",
    "license": "AGPL-3",
    "depends": ["base_setup"],
    "data": [
        "views/res_config_settings_view.xml",
    ],
    "installable": True,
    "application": False,
    "external_dependencies": {
        "python": ["pyjwt"],
    },
}
