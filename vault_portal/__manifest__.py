# Copyright 2026 INVITU (<https://www.invitu.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Vault Portal",
    "summary": "Portal access to shared vaults, per-user E2E encrypted",
    "license": "AGPL-3",
    "version": "18.0.1.0.0",
    "website": "https://github.com/OCA/server-auth",
    "author": "INVITU, Odoo Community Association (OCA)",
    "category": "Vault",
    "depends": ["vault", "portal", "auth_totp"],
    "data": [
        "security/ir.model.access.csv",
        "security/ir_rule.xml",
        "views/portal_templates.xml",
        "views/res_config_settings_views.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "vault/static/src/common/utils.esm.js",
            "vault/static/src/common/vault_utils_service.esm.js",
            "vault/static/src/backend/vault.esm.js",
            "vault_portal/static/src/frontend/vault_key_manager.esm.js",
            "vault_portal/static/src/frontend/vault_detail.esm.js",
            "vault_portal/static/src/xml/vault_key_manager.xml",
            "vault_portal/static/src/xml/vault_detail.xml",
            "vault_portal/static/src/scss/portal.scss",
        ],
    },
}
