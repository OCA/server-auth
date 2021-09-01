# Copyright 2016-2017 LasLabs Inc.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

{
    'name': 'MFA Support',
    'summary': 'Allows users to enable MFA and add optional trusted devices',
    'version': '12.0.1.1.0',
    'category': 'Tools',
    'website': 'https://github.com/OCA/server-auth',
    'author': 'LasLabs, Odoo Community Association (OCA)',
    'license': 'LGPL-3',
    'application': False,
    'installable': True,
    'external_dependencies': {
        'python': ['pyotp'],
    },
    'depends': [
        'web',
    ],
    'data': [
        'data/ir_config_parameter.xml',
        'security/ir.model.access.csv',
        'security/res_users_authenticator_security.xml',
        'wizards/res_users_authenticator_create.xml',
        'views/auth_totp.xml',
        'views/res_users.xml',
    ],
}
