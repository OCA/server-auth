# Copyright 2018 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

{
    'name': 'Assign roles via HTTP Header',
    'summary': 'Assign roles found in the HTTP header, to the connected user',
    'version': '11.0.1.0.0',
    'category': 'Tools',
    'website': 'https://github.com/OCA/server-auth',
    'author': 'Camptocamp, Odoo Community Association (OCA)',
    'license': 'AGPL-3',
    'application': False,
    'installable': True,
    'depends': [
        'auth_from_http_remote_user',
        'base_user_role',
        ],
    'data': [
        'views/res_users_role.xml',
        ],
}
