# Copyright 2026 360ERP (<https://www.360erp.com>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "360 ERP - Auth User Role SAML glue module",
    "version": "18.0.1.0.0",
    "author": "360 ERP, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/server-auth",
    "license": "AGPL-3",
    "depends": [
        "auth_saml",
        "auth_user_role",
    ],
    "data": [
        "views/auth_saml_provider_views.xml",
    ],
    "auto_install": True,
}
