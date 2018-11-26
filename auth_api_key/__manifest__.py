# -*- coding: utf-8 -*-
# Copyright 2018 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Auth Api Key',
    'summary': """
        Authenticate http requests from an API key""",
    'version': '10.0.1.0.0',
    'license': 'AGPL-3',
    'author': 'ACSONE SA/NV,Odoo Community Association (OCA)',
    'website': 'https://acsone.eu/',
    'depends': [
        'keychain'
    ],
    'data': [
        'security/auth_api_key.xml',
        'views/auth_api_key.xml',
    ],
    'demo': [
    ],
}
