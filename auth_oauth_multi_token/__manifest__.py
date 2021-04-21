# Copyright 2016 Florent de Labarre
# Copyright 2017 Camptocamp
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

{
    "name": "OAuth Multi Token",
    "version": "13.0.2.0.0",
    "license": "AGPL-3",
    "author": "Florent de Labarre, Camptocamp, Odoo Community Association (OCA)",
    "summary": """Allow multiple connection with the same OAuth account""",
    "category": "Tool",
    "website": "https://github.com/OCA/server-auth",
    "depends": ["auth_oauth"],
    "data": [
        "security/ir.model.access.csv",
        "views/auth_oauth_multi_token.xml",
        "views/res_users.xml",
    ],
    "installable": True,
}
