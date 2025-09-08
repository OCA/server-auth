# Copyright Daniel Reis (https://launchpad.com/~dreis-pt)
# Copyright 2021 Tecnativa - João Marques
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "LDAP mapping for user name and e-mail",
    "version": "18.0.1.0.0",
    "depends": ["auth_ldap"],
    "author": "Daniel Reis," "Odoo Community Association (OCA)",
    "maintainers": ["joao-p-marques"],
    "website": "https://github.com/OCA/server-auth",
    "license": "AGPL-3",
    "category": "Tools",
    "data": ["views/res_company_ldap.xml"],
    "installable": True,
}
