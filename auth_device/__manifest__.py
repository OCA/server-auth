# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Auth Device",
    "summary": "Allows users to log in through an external device.",
    "version": "19.0.1.0.0",
    "license": "AGPL-3",
    "author": "ACSONE SA/NV,Odoo Community Association (OCA)",
    "maintainers": ["FrancoMaxime"],
    "website": "https://github.com/OCA/server-auth",
    "depends": [
        "web",
    ],
    "data": [
        "views/auth_device_connection.xml",
        "views/res_users_views.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "auth_device/static/src/interactions/*",
        ],
    },
}
