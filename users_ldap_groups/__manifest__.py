# Copyright 2012-2018 Therp BV <https://therp.nl>
# Copyright 2018 Brainbean Apps <https://brainbeanapps.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
{
    'name': 'LDAP groups assignment',
    'version': '12.0.1.0.0',
    'depends': [
        'auth_ldap',
    ],
    'author':
        'Therp BV, '
        'Odoo Community Association (OCA)',
    'license': 'AGPL-3',
    'summary':
        'Adds user accounts to groups based on rules defined '
        'by the administrator.',
    'category': 'Authentication',
    'data': [
        'views/res_company_ldap_views.xml',
        'security/ir.model.access.csv',
    ],
    'external_dependencies': {
        'python': [
            'ldap'
        ],
    },
}
