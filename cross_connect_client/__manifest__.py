# Copyright 2024 Akretion (http://www.akretion.com).
# @author Florian Mounier <florian.mounier@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Cross Connect Client",
    "version": "16.0.1.0.0",
    "author": "Akretion, Odoo Community Association (OCA)",
    "summary": "Cross Connect Client allows to connect to a "
    "Cross Connect Server enabled odoo instance.",
    "category": "Tools",
    "depends": ["server_environment"],
    "website": "https://github.com/OCA/server-auth",
    "data": [
        "security/ir_model_access.xml",
        "views/cross_connect_server_views.xml",
    ],
    "maintainers": ["paradoxxxzero"],
    "demo": [],
    "installable": True,
    "license": "AGPL-3",
}
