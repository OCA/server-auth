# SPDX-FileCopyrightText: 2025 Coop IT Easy SC
#
# SPDX-License-Identifier: AGPL-3.0-or-later

{
    "name": "Auth Sign Up Recaptcha v2",
    "summary": "Add recaptcha v2 to sign up form",
    "version": "16.0.1.0.0",
    "category": "Authentication",
    "website": "https://github.com/OCA/server-auth",
    "author": "Coop IT Easy SC, Odoo Community Association (OCA)",
    "maintainers": ["remytms"],
    "license": "AGPL-3",
    "depends": [
        "auth_signup",
        "website_recaptcha_v2",
    ],
    "data": [
        "views/auth_signup_login_templates.xml",
    ],
    "demo": [],
}
