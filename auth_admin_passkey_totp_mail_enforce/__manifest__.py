# Copyright 2024 360ERP (<https://www.360erp.com>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Authentification - Disable 2FA if Passkey",
    "summary": " Disable 2FA if Passkey is being used",
    "version": "17.0.1.0.0",
    "category": "base",
    "author": "360ERP,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/server-auth",
    "license": "AGPL-3",
    "depends": ["auth_admin_passkey", "auth_totp_mail_enforce"],
    "installable": True,
    "auto_install": True,
}
