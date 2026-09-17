# Copyright 2026 360ERP (<https://www.360erp.com>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "360 ERP - Auth User Role",
    "version": "18.0.1.0.0",
    "author": "360 ERP, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/server-auth",
    "license": "AGPL-3",
    "depends": [
        "base_user_role",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/auth_user_role_mapping_views.xml",
    ],
    "post_init_hook": "post_init_hook",
}
