# Copyright (C) 2020 GlodoUK <https://www.glodo.uk/>
# Copyright (C) 2010-2016 XCG Consulting <http://odoo.consulting>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Saml2 Authentication",
    "version": "14.0.1.0.1",
    "category": "Tools",
    "author": "XCG Consulting, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/server-auth",
    "license": "AGPL-3",
    "depends": ["base_setup"],
    "external_dependencies": {"python": ["pysaml2"], "deb": ["xmlsec1"]},
    "demo": [],
    "data": [
        "security/ir.model.access.csv",
        "views/auth_saml.xml",
        "views/res_config_settings.xml",
        "views/res_users.xml",
    ],
    "installable": True,
    "auto_install": False,
}
