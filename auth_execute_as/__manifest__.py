# Copyright 2026 Kencove (https://www.kencove.com).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Auth Execute As",
    "summary": "Execute API calls as a specific user with whitelist-based access control",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": "Kencove, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/server-auth",
    "category": "Tools",
    "depends": ["base"],
    "data": [
        "security/ir.model.access.csv",
        "views/auth_api_whitelist_views.xml",
        "views/auth_api_whitelist_line_views.xml",
        "views/auth_api_client_views.xml",
        "views/auth_api_log_views.xml",
        "data/ir_cron_data.xml",
    ],
    "installable": True,
}
