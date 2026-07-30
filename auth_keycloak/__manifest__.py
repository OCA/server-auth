# Copyright 2018 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

{
    "name": "Keycloak auth integration",
    "summary": "Integrate Keycloak into your SSO",
    "version": "16.0.1.0.0",
    "category": "Tools",
    "website": "https://github.com/OCA/server-auth",
    "author": "Camptocamp, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "depends": [
        "auth_oidc",
    ],
    "data": [
        "security/ir.model.access.csv",
        "wizard/auth_keycloak_sync_wiz.xml",
        "wizard/auth_keycloak_create_wiz.xml",
        "views/auth_oauth_views.xml",
        "views/res_users_views.xml",
    ],
}
