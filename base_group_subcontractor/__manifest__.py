# Copyright 2026 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
{
    "name": "Extra user type",
    "summary": "Extra user type group for restricted access to backend",
    "version": "18.0.1.0.0",
    "development_status": "Beta",
    "category": "Tools",
    "website": "https://github.com/OCA/server-auth",
    "author": "Tecnativa, Odoo Community Association (OCA)",
    "maintainers": ["pedrobaeza"],
    "license": "AGPL-3",
    "depends": [
        "mail",
        "web_editor",
    ],
    "demo": [
        "demo/res_users_demo.xml",
    ],
    "data": [
        "security/base_group_subcontractor_security.xml",
        "security/ir.model.access.csv",
        "data/ir_ui_menu_data.xml",
    ],
}
