# Copyright 2021 Camptocamp SA
# @author: Simone Orsi <simone.orsi@camptocamp.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    "name": "Auth Users API key server environment",
    "summary": """
Configure user api keys (`res.users.apikeys`) via server env.
    """,
    "version": "14.0.1.1.0",
    "license": "LGPL-3",
    "website": "https://github.com/OCA/server-auth",
    "author": "Camptocamp,Odoo Community Association (OCA)",
    "depends": ["base", "server_environment"],
    "data": [
        "security/ir.model.access.csv",
        "views/res_users_apikeys.xml",
    ],
}
