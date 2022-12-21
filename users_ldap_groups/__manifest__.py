# Copyright 2012-2018 Therp BV <https://therp.nl>
# Copyright 2018 Brainbean Apps <https://brainbeanapps.com>
# Copyright 2021 Tecnativa - João Marques
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
{
    "name": "LDAP groups assignment",
    "version": "15.0.1.0.0",
    "depends": ["auth_ldap"],
    "author": "Therp BV, " "Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/server-auth",
    "license": "AGPL-3",
    "summary": "Adds user accounts to groups based on rules defined "
    "by the administrator.",
    "category": "Authentication",
    "data": ["views/res_company_ldap_views.xml", "security/ir.model.access.csv"],
    "external_dependencies": {"python": ["python-ldap"]},
}
