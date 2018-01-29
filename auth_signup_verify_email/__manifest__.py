# Copyright 2015 Antiun Ingeniería, S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "Verify email at signup",
    "summary": "Force uninvited users to use a good email for signup",
    "version": "11.0.1.0.0",
    "category": "Authentication",
    "website": "https://github.com/OCA/server-auth",
    "author": "Antiun Ingeniería S.L., "
              "Tecnativa, "
              "Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "depends": [
        "auth_signup",
    ],
    "external_dependencies": {
        "python": [
            "lxml",
            "validate_email",
        ],
    },
    "data": [
        "views/signup.xml",
    ],
    'installable': True,
}
