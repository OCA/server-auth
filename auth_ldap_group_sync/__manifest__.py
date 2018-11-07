# Copyright 2018 Brainbean Apps (https://brainbeanapps.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    'name': 'LDAP Group Sync',
    'version': '12.0.1.0.0',
    'category': 'Tools',
    'website': 'https://github.com/OCA/server-auth',
    'author':
        'Brainbean Apps, '
        'Odoo Community Association (OCA)',
    'license': 'AGPL-3',
    'installable': True,
    'application': False,
    'summary': (
        'Allows updating users’ group membership based on LDAP group'
        ' membership'
    ),
    'depends': [
        'auth_ldap',
    ],
    'external_dependencies': {
        'python': [
            'ldap',
        ],
    },
    'data': [
        'security/ir.model.access.csv',
        'data/ir_cron_data.xml',
        'views/res_company_ldap_views.xml',
        'views/ldap_group_mapping_views.xml',
    ],
}
