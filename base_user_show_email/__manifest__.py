# Copyright 2019 Camptocamp
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    "name": "Base User Show Email",
    "version": "18.0.1.0.0",
    "category": "Tools",
    "website": "https://github.com/OCA/server-auth",
    "author": "Camptocamp, " "Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "installable": True,
    "application": False,
    "summary": "Untangle user login and email",
    "depends": ["base", "web"],
    "data": ["views/res_users_view.xml", "views/login_layout.xml"],
}
