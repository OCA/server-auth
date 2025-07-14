# © 2019 Savoir-faire Linux
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Auth SAML Create User",
    "summary": """
        This module extends the functionality of Auth SAML to support
        the automatic creation of SAML users when they don't exist in odoo.""",
    "version": "18.0.1.0.0",
    "category": "Tools",
    "sequence": 20,
    "author": "Savoir-faire Linux, Odoo Community Association (OCA), Smile",
    "maintainers": ["eilst"],
    "website": "https://github.com/OCA/server-auth",
    "license": "AGPL-3",
    "depends": [
        "auth_saml",
    ],
    "data": [
        "views/auth_saml.xml",
    ],
    "demo": [],
    "test": [],
    "auto_install": False,
    "installable": True,
    "application": False,
}
