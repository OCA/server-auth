# © 2021 Florian Kantelberg - initOS GmbH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Vault",
    "summary": "Password vault integration in Odoo",
    "license": "AGPL-3",
    "version": "14.0.1.5.0",
    "website": "https://github.com/OCA/server-auth",
    "application": True,
    "author": "initOS GmbH, Odoo Community Association (OCA)",
    "category": "Vault",
    "depends": ["web"],
    "data": [
        "security/ir.model.access.csv",
        "security/ir_rule.xml",
        "views/assets.xml",
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
    "qweb": ["static/src/xml/templates.xml"],
}
