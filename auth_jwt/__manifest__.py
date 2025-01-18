# Copyright 2021 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    "name": "Auth JWT",
    "summary": """
        JWT bearer token authentication.""",
    "version": "18.0.1.0.0",
    "license": "LGPL-3",
    "author": "ACSONE SA/NV,Odoo Community Association (OCA)",
    "maintainers": ["sbidoul"],
    "website": "https://github.com/OCA/server-auth",
    "depends": [],
    "external_dependencies": {"python": ["pyjwt", "cryptography"]},
    "data": ["security/ir.model.access.csv", "views/auth_jwt_validator_views.xml"],
    "demo": [],
    "installable": True,
    "application": False,
    "auto_install": False,
}
