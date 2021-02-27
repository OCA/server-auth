# Copyright (C) 2010-2016 XCG Consulting <http://odoo.consulting>
# Copyright (C) 2020 GlodoUK <https://www.glodo.uk/>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Saml2 Authentication',
    'version': '13.0.1.0.0',
    'category': 'Tools',
    'author': 'XCG Consulting, Vauxoo, Odoo Community Association (OCA)',
    'website': 'https://github.com/OCA/server-auth',
    'license': 'AGPL-3',
    'depends': [
        'base_setup',
    ],
    "external_dependencies": {
        "python": ["saml2"],
    },
    'data': [
        'security/ir.model.access.csv',
        'views/auth_saml.xml',
        'views/base_settings.xml',
        'views/res_users.xml',
    ],
    "demo": [
        'demo/auth_saml_provider.xml',
    ],
    'installable': True,
    'auto_install': False,
}
