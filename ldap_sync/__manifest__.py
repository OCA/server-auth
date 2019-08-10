# Copyright 2019 Brainbean Apps (https://brainbeanapps.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    'name': 'LDAP Sync',
    'version': '12.0.1.0.0',
    'category': 'Tools',
    'website': 'https://github.com/OCA/server-auth',
    'author':
        'Brainbean Apps, '
        'Odoo Community Association (OCA)',
    'license': 'AGPL-3',
    'installable': True,
    'application': False,
    'summary': 'Sync user directory with LDAP server',
    'depends': [
        'auth_ldap',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/cron.xml',
        'views/res_company_ldap_group_mapping.xml',
        'views/res_company_ldap_group.xml',
        'views/res_company_ldap_user.xml',
        'views/res_company_ldap.xml',
        'views/res_users.xml',
    ],
}
