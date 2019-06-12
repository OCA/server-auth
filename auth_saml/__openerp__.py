# -*- coding: utf-8 -*-
# Copyright (C) 2010-2019 XCG Consulting <http://odoo.consulting>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Saml2 Authentication',
    'version': '9.0.1.0.0',
    'category': 'Tools',
    'author': 'XCG Consulting, Odoo Community Association (OCA)',
    'maintainer': 'XCG Consulting',
    'website': 'http://odoo.consulting',
    'license': 'AGPL-3',
    'depends': [
        'base',
        'base_setup',
        'web',
        'auth_crypt',
        'auth_signup'
    ],
    'data': [
        'data/auth_saml.xml',
        'data/ir_config_parameter.xml',
        'security/ir.model.access.csv',
        'views/auth_saml.xml',
        'views/base_settings.xml',
        'views/res_users.xml',
    ],
    'installable': True,
    'external_dependencies': {
        'python': ['lasso'],  # >= 2.6.0
    },
    'development_status': 'stable',
}
