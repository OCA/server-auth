# Copyright 2012-2018 Therp BV <https://therp.nl>.
# Copyright 2021 Tecnativa - João Marques
# License AGPL-3.0 or later (http://www.gnu.org/licenses/gpl.html).
{
    "name": "LDAP Populate",
    "version": "13.0.1.0.0",
    "author": "Therp BV, Odoo Community Association (OCA)",
    "maintainers": ["joao-p-marques"],
    "license": "AGPL-3",
    "category": "Tools",
    "depends": ["auth_ldap"],
    "external_dependencies": {"python": ["python-ldap"]},
    "data": ["views/users_ldap.xml", "views/populate_wizard.xml"],
    "installable": True,
}
