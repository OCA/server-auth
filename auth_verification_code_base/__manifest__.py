# Copyright 2022 Akretion
# Copyright 2022 Toodigit
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Auth Verification Code Base",
    "summary": """
        Base functionality for verification code""",
    "version": "13.0.1.0.0",
    "license": "AGPL-3",
    "author": "Akretion,Odoo Community Association (OCA)",
    "depends": ["auth_signup"],
    "website": "https://github.com/OCA/server-auth",
    "data": [
        "data/data.xml",
        "security/ir.model.access.csv",
        "views/auth_verification_code.xml",
        "views/auth_verification_code_log.xml",
        "views/res_users.xml",
        "views/templates.xml",
    ],
    "demo": ["demo/demo.xml"],
    "external_dependencies": {"python": ["freezegun"]},
}
