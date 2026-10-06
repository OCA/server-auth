# Copyright 2026 Lorenzo Battistini
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    "name": "OAuth Authorization Server",
    "summary": "Let applications obtain OAuth 2.1 access tokens for Odoo users",
    "version": "16.0.1.0.0",
    "category": "Tools",
    "license": "LGPL-3",
    "author": "Lorenzo Battistini, Odoo Community Association (OCA)",
    "maintainers": ["eLBati"],
    "website": "https://github.com/OCA/server-auth",
    "development_status": "Alpha",
    "depends": ["auth_jwt", "base_setup"],
    "external_dependencies": {"python": ["pyjwt"]},
    "data": [
        "security/ir.model.access.csv",
        "security/oauth_server_security.xml",
        "views/oauth_server_resource_views.xml",
        "views/oauth_server_client_views.xml",
        "views/oauth_server_authorization_views.xml",
        "views/auth_jwt_validator_views.xml",
        "views/res_users_views.xml",
        "views/res_config_settings_views.xml",
        "views/oauth_server_menus.xml",
        "views/oauth_server_templates.xml",
    ],
    "post_init_hook": "post_init_hook",
    "installable": True,
}
