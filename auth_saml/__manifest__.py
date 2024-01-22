# Copyright (C) 2020 GlodoUK <https://www.glodo.uk/>
# Copyright (C) 2010-2016, 2022 XCG Consulting <http://odoo.consulting>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "SAML2 Authentication",
    "version": "15.0.1.4.3",
    "category": "Tools",
    "author": "XCG Consulting, Odoo Community Association (OCA)",
    "maintainers": ["vincent-hatakeyama"],
    "website": "https://github.com/OCA/server-auth",
    "license": "AGPL-3",
    "depends": ["base_setup", "web"],
    "external_dependencies": {
        # Place an upper bound on cryptography version to be compatible with
        # pyopenssl 19 mentioned in Odoo 15's requirements.txt. If we don't do
        # this, installing this module will try to upgrade cryptography to the latest
        # version because the minimum required version in pysaml2 (>=3.1) is greater than
        # version 2.6 (from Odoo's requirement.txt). Since cryptography/pyopenssl don't
        # declare minimum supported versions, this lead to inconsistencies.
        # https://github.com/OCA/server-auth/issues/424
        "python": ["pysaml2", "cryptography<37"],
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
