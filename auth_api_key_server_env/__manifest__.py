# Copyright 2021 Camptocamp SA
# @author: Simone Orsi <simone.orsi@camptocamp.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    "name": "Auth API key server environment",
    "summary": """
Configure api keys via server env.

This can be very useful to avoid mixing your keys between your various
environments when restoring databases. All you have to do is to add a new
section to your configuration file according to the following convention:
    """,
    "version": "18.0.1.0.0",
    "development_status": "Production/Stable",
    "license": "LGPL-3",
    "website": "https://github.com/OCA/server-auth",
    "author": "Camptocamp,Odoo Community Association (OCA)",
    "depends": ["auth_api_key", "server_environment"],
    "data": [],
}
