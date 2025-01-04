# Copyright 2025 Hunki Enterprises BV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)

{
    "name": "IP based MFA bypass (with auth_totp_mail_enforce)",
    "summary": "Make auth_totp_bypass_ip_range compatible with auth_totp_mail_enforce",
    "version": "16.0.1.0.0",
    "development_status": "Alpha",
    "category": "Hidden",
    "website": "https://github.com/OCA/server-auth",
    "author": "Hunki Enterprises BV, Odoo Community Association (OCA)",
    "maintainers": ["hbrunn"],
    "license": "AGPL-3",
    "auto_install": True,
    "depends": [
        "auth_totp_mail_enforce",
        "auth_totp_bypass_ip_range",
    ],
    "data": [],
    "demo": [],
}
