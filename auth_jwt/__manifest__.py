# Copyright 2021 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Auth JWT",
    "summary": """
        JWT bearer token authentication.""",
    "version": "11.0.1.0.2",
    "license": "AGPL-3",
    "author": "ACSONE SA/NV,Odoo Community Association (OCA)",
    "maintainers": ["sbidoul"],
    "website": "https://github.com/OCA/server-auth",
    "depends": [],
    "external_dependencies": {"python": ["jwt", "cryptography"]},
    "data": ["security/ir.model.access.csv", "views/auth_jwt_validator_views.xml"],
    "demo": [],
}
