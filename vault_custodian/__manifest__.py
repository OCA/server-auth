# © 2026 Nitrokey GmbH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Vault - Custodian",
    "summary": "Enforce mandatory custodians on newly created vaults",
    "license": "AGPL-3",
    "version": "18.0.1.0.0",
    "website": "https://github.com/OCA/server-auth",
    "application": False,
    "author": "Nitrokey GmbH, Odoo Community Association (OCA)",
    "category": "Vault",
    "depends": ["vault"],
    "data": [
        "views/res_config_settings_views.xml",
    ],
}
