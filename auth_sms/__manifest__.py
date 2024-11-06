# Copyright 2019 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
{
    "name": "Two factor authentication via SMS",
    "version": "16.0.1.0.0",
    "author": "Therp BV,Odoo Community Association (OCA)",
    "maintainers": ["NL66278"],
    "license": "AGPL-3",
    "category": "Tools",
    "website": "https://github.com/OCA/server-auth",
    "summary": "Allow users to turn on two factor authentication via SMS",
    "depends": [
        "mail",
    ],
    "demo": [
        "demo/res_users.xml",
        "demo/sms_provider.xml",
    ],
    "data": [
        "views/sms_provider.xml",
        "views/res_users.xml",
        "security/ir_rule.xml",
        "templates/template_code.xml",
        "security/ir.model.access.csv",
    ],
}
