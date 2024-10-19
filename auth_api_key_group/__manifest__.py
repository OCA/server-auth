# Copyright 2021 Camptocamp SA
# @author: Simone Orsi <simone.orsi@camptocamp.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    "name": "Auth API key group",
    "summary": """
Allow grouping API keys together.

Grouping per se does nothing. This feature is supposed to be used by other modules
to limit access to services or records based on groups of keys.
    """,
    "version": "18.0.1.0.0",
    "development_status": "Beta",
    "license": "LGPL-3",
    "website": "https://github.com/OCA/server-auth",
    "author": "Camptocamp,Odoo Community Association (OCA)",
    "maintainers": ["simahawk"],
    "depends": ["auth_api_key"],
    "data": [
        "security/ir.model.access.csv",
        "views/auth_api_key_view.xml",
        "views/auth_api_key_group_view.xml",
    ],
}
