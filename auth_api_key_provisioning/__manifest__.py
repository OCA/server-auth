# Copyright 2026 Keboola
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    "name": "Auth API Key Provisioning",
    "summary": """
        Admin-gated minting of short-lived, rpc-scoped API keys on behalf of
        another (non-elevated) internal user, for delegated per-user identity.""",
    "version": "18.0.1.0.0",
    "license": "LGPL-3",
    "author": "Keboola, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/server-auth",
    "development_status": "Beta",
    "maintainers": ["manana2520"],
    "category": "Tools",
    "depends": ["base"],
    "data": [
        "security/auth_api_key_provisioning_groups.xml",
        "security/ir.model.access.csv",
        "data/ir_config_parameter.xml",
        "data/ir_cron.xml",
        "views/auth_api_key_provisioning_log_views.xml",
    ],
}
