# Copyright (C) 2017 Creu Blanca
# Copyright (C) 2018 Brainbean Apps
# Copyright 2020 CorporateHub (https://corporatehub.eu)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    "name": "LDAPS authentication",
    "version": "15.0.1.0.0",
    "category": "Tools",
    "website": "https://github.com/OCA/server-auth",
    "author": "CorporateHub, " "Creu Blanca, " "Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "installable": True,
    "application": False,
    "summary": "Allows to use LDAP over SSL authentication",
    "depends": ["auth_ldap"],
    "data": ["views/res_company_ldap_views.xml"],
    "external_dependencies": {"python": ["python-ldap"]},
}
