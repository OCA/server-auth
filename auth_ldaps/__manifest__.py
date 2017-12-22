# Copyright (C) 2017 Creu Blanca
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    'name': 'LDAPS authentication',
    'version': '11.0.1.0.0',
    'category': 'Tools',
    'website': 'https://github.com/OCA/server-auth',
    'author': 'Creu Blanca, Odoo Community Association (OCA)',
    'license': 'AGPL-3',
    'installable': True,
    'application': False,
    'summary': 'Allows to use LDAP over SSL authentication',
    'depends': [
        'auth_ldap',
    ],
    'data': [
        'views/res_company_ldap_views.xml',
    ],
}
