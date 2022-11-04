# Copyright Daniel Reis (https://launchpad.com/~dreis-pt)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/gpl.html).

{
    'name': "LDAP mapping for user name and e-mail",
    'version': "12.0.1.0.1",
    'depends': ["auth_ldap"],
    'author': "Daniel Reis,"
              "Odoo Community Association (OCA)",
    'website': 'https://github.com/OCA/server-auth',
    'license': 'AGPL-3',
    'category': "Tools",
    'data': [
        'views/res_company_ldap.xml',
    ],
    'installable': True,
}
