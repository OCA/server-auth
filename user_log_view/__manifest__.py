# Copyright 2019 Denis Mudarisov (IT-Projects LLC)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
{
    "name": "User's Log Viewer",
    "summary": "Allow to see user's actions log",
    "version": "14.0.1.0.0",
    "development_status": "Production/Stable",
    "category": "Extra Tools",
    "website": "https://github.com/OCA/server-auth",
    "author": "IT-Projects LLC, Odoo Community Association (OCA)",
    "maintainers": ["trojikman"],
    "license": "LGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "base",
    ],
    "data": [
        "views/res_users_views.xml",
    ],
}
