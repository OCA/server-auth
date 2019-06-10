# © 2019 Savoir-faire Linux
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    'name': "Auth SAML Create User",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,
    'author': 'Savoir-faire Linux',
    'maintainer': 'Savoir-faire Linux',
    'website': 'http://www.savoirfairelinux.com',
    'license': 'LGPL-3',
    'category': 'Tools',
    'version': '11.1',
    'depends': [
        'base',
        'auth_saml'
    ],
    'data': [
        'views/auth_saml.xml',
    ],
}
