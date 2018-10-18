# Copyright (C) 2018 Brainbean Apps (https://brainbeanapps.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    'name': 'LDAP Attributes Sync',
    'version': '12.0.1.0.0',
    'category': 'Tools',
    'website': 'https://github.com/OCA/server-auth',
    'author':
        'Braibean Apps (https://brainbeanapps.com), '
        'Odoo Community Association (OCA)',
    'license': 'AGPL-3',
    'installable': True,
    'application': False,
    'summary': 'Allows to update users’ fields from LDAP attributes',
    'depends': [
        'auth_ldap',
    ],
    'external_dependencies': {
        'python': [
            'ldap',
        ],
    },
    'data': [
        'views/res_company_ldap_views.xml',
    ],
}
