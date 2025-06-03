# Copyright 2024 Akretion (http://www.akretion.com).
# @author Florian Mounier <florian.mounier@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Cross Connect Server",
    "version": "16.0.1.0.1",
    "author": "Akretion, Odoo Community Association (OCA)",
    "summary": "Cross Connect Server allows Cross Connect Client to connect to it.",
    "category": "Tools",
    "depends": ["extendable_fastapi", "server_environment"],
    "website": "https://github.com/OCA/server-auth",
    "data": [
        "security/res_groups.xml",
        "security/ir_model_access.xml",
        "views/fastapi_endpoint_views.xml",
    ],
    "maintainers": ["paradoxxxzero"],
    "demo": [],
    "installable": True,
    "license": "AGPL-3",
    "external_dependencies": {
        "python": ["pyjwt"],
    },
}
