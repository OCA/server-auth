# Copyright 2026 ForgeFlow S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Scheduled Session Logout",
    "summary": "Force logout of all active user sessions on a schedule",
    "version": "18.0.1.0.0",
    "category": "Tools",
    "author": "ForgeFlow, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/server-auth",
    "license": "AGPL-3",
    "depends": ["base"],
    "data": [
        "security/auth_session_scheduled_logout_groups.xml",
        "data/ir_cron_data.xml",
    ],
    "post_init_hook": "post_init_hook",
    "installable": True,
}
