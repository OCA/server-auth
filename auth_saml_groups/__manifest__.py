# © 2019 Savoir-faire Linux
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    'name': "Auth SAML Groups",

    'summary': """
        This module extends the functionality of Auth SAML
        to support the mapping between SAML groups and odoo groups.""",
    'author': 'Savoir-faire Linux, Odoo Community Association (OCA)',
    'maintainer': 'Savoir-faire Linux',
    'website': 'https://github.com/OCA/server-auth',
    'maintainers': ['eilst'],
    'license': 'AGPL-3',
    'category': 'Tools',
    'version': '11.0.1.0.0',
    'depends': [
        'base',
        'auth_saml'
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/auth_saml.xml',
        'data/auth_saml_groups.xml',
    ],
}
