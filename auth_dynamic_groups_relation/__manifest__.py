# -*- coding: utf-8 -*-
# Copyright 2019 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
{
    "name": "Partner relation based dynamic groups",
    "version": "10.0.0.1.0",
    "author": "Odoo Community Association (OCA),Therp BV",
    "license": "AGPL-3",
    "complexity": "normal",
    'summary': 'Have group membership based on partner relations',
    "category": "Tools",
    "website": "https://github.com/OCA/server-auth",
    "depends": [
        'auth_dynamic_groups',
        'partner_multi_relation',
    ],
    "data": [
        'views/res_groups.xml',
    ],
}
