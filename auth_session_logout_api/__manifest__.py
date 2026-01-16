# Copyright 2026 Kencove (https://www.kencove.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Force User Session Logout",
    "summary": "Force logout user sessions via secure API endpoint",
    "version": "16.0.1.0.0",
    "category": "Tools",
    "website": "https://github.com/OCA/server-auth",
    "author": "Kencove, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "installable": True,
    "depends": [
        "base_setup",
    ],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "views/auth_session_logout_audit_views.xml",
        "views/res_config_settings_views.xml",
    ],
}
