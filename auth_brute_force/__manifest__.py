# Copyright 2015 GRAP - Sylvain LE GAL
# Copyright 2017 Tecnativa - David Vidal
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "Authentication - Brute-Force Filter",
    "version": "15.0.1.0.0",
    "category": "Tools",
    "summary": "Track Authentication Attempts and Prevent Brute-force Attacks",
    "author": "Nitrokey GmbH,"
    "GRAP, "
    "Tecnativa, "
    "Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/server-auth",
    "license": "AGPL-3",
    "depends": [
        "base",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/view.xml",
        "views/action.xml",
        "views/menu.xml",
    ],
    "installable": True,
}
