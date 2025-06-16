# Copyright 2025 Alberto Martínez <alberto.martinez@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "API Key Scope Editable",
    "summary": "Set the API Key scope at creation",
    "version": "17.0.1.0.0",
    "category": "Technical",
    "website": "https://github.com/OCA/server-auth",
    "author": "Sygel, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "base",
    ],
    "data": [
        "wizards/res_users_apikeys_description_views.xml",
    ],
}
