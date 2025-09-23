# Copyright (C) 2020 GlodoUK <https://www.glodo.uk/>
# Copyright (C) 2010-2016, 2022 XCG Consulting <http://odoo.consulting>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "SAML2 Authentication",
    "version": "18.0.1.1.0",
    "category": "Tools",
    "author": "XCG Consulting, Odoo Community Association (OCA)",
    "maintainers": ["vincent-hatakeyama"],
    "website": "https://github.com/OCA/server-auth",
    "license": "AGPL-3",
    "depends": ["base_setup", "web"],
    "external_dependencies": {
        "python": ["pysaml2"],
        "bin": ["xmlsec1"],
        # special definition used by OCA to install packages
        "deb": ["xmlsec1"],
    },
    "demo": [],
    "data": [
        "data/ir_config_parameter.xml",
        "security/ir.model.access.csv",
        "views/auth_saml.xml",
        "views/res_config_settings.xml",
        "views/res_users.xml",
    ],
    "installable": True,
    "auto_install": False,
    "development_status": "Beta",
}
