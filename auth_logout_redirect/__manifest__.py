# Copyright 2025 XCG SAS
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Logout Redirect",
    "summary": "Redirect on logout",
    "version": "17.0.1.0.0",
    "development_status": "Alpha",
    "category": "Tools",
    "website": "https://github.com/OCA/server-auth",
    "author": "XCG SAS, Odoo Community Association (OCA)",
    "maintainers": ["vincent-hatakeyama"],
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "preloadable": True,
    "depends": ["web"],
    "data": [
        "templates/webclient.xml",
    ],
}
