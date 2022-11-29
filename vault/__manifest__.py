# © 2021 Florian Kantelberg - initOS GmbH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Vault",
    "summary": "Password vault integration in Odoo",
    "license": "AGPL-3",
    "version": "15.0.1.6.1",
    "website": "https://github.com/OCA/server-auth",
    "application": True,
    "author": "initOS GmbH, Odoo Community Association (OCA)",
    "category": "Vault",
    "depends": ["base_setup", "web"],
    "data": [
        "security/ir.model.access.csv",
        "security/ir_rule.xml",
        "views/res_config_settings_views.xml",
        "views/res_users_views.xml",
        "views/vault_entry_views.xml",
        "views/vault_field_views.xml",
        "views/vault_file_views.xml",
        "views/vault_log_views.xml",
        "views/vault_inbox_views.xml",
        "views/vault_right_views.xml",
        "views/vault_views.xml",
        "views/menuitems.xml",
        "views/templates.xml",
        "wizards/vault_export_wizard.xml",
        "wizards/vault_import_wizard.xml",
        "wizards/vault_send_wizard.xml",
        "wizards/vault_store_wizard.xml",
    ],
    "assets": {
        "vault.assets_frontend": [
            "vault/static/src/common/*.js",
            "vault/static/src/frontend/*.js",
        ],
        "web.assets_backend": [
            "vault/static/lib/**/*.min.js",
            "vault/static/src/common/*.js",
            "vault/static/src/backend/*.scss",
            "vault/static/src/backend/*.js",
            "vault/static/src/legacy/vault_controller.js",
            "vault/static/src/legacy/vault_widget.js",
        ],
        "web.assets_qweb": [
            "vault/static/src/**/*.xml",
        ],
        "web.tests_assets": [
            "vault/static/tests/**/*.js",
        ],
    },
}
