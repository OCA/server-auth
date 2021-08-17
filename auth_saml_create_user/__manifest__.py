# © 2019 Savoir-faire Linux
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': "Auth SAML Create User",
    'summary': """
        This module extends the functionality of Auth SAML to support
        the automatic creation of SAML users when they don't exist in odoo.""",
    'author': 'Savoir-faire Linux, Odoo Community Association (OCA)',
    'maintainers': ['eilst'],
    'website': 'https://github.com/OCA/server-auth',
    'license': 'AGPL-3',
    'category': 'Tools',
    'version': '11.0.1.0.1',
    'depends': [
        'auth_saml'
    ],
    'data': [
        'data/auth_saml_create_user.xml',
        'views/auth_saml.xml',
    ],
    'development_status': 'Production/Stable',
}
