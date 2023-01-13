# © 2021 Florian Kantelberg - initOS GmbH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Vault - Share",
    "summary": "Implementation of a mechanism to share secrets",
    "license": "AGPL-3",
    "version": "14.0.1.2.1",
    "website": "https://github.com/OCA/server-auth",
    "application": False,
    "author": "initOS GmbH, Odoo Community Association (OCA)",
    "category": "Vault",
    "depends": ["vault"],
    "data": [
        "data/ir_cron.xml",
        "security/ir.model.access.csv",
        "security/ir_rule.xml",
        "views/assets.xml",
        "views/menuitems.xml",
        "views/res_config_settings_views.xml",
        "views/templates.xml",
        "views/vault_share_views.xml",
    ],
    "qweb": ["static/src/xml/templates.xml"],
}
