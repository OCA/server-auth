# Copyright 2017 LasLabs Inc.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html)

{
    'name': 'MFA and Password Security Compatibility',
    'summary': 'auth_totp and password_security compatibility',
    'version': '11.0.1.0.0',
    'category': 'Hidden',
    'website': 'https://github.com/OCA/server-auth',
    'author': 'LasLabs, Odoo Community Association (OCA)',
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': True,
    'depends': [
        'auth_totp',
        'password_security',
    ],
}
