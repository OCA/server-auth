# Copyright 2023 glueckkanja AG (https://www.glueckkanja.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Authentication OpenID Connect on Portal",
    "summary": "Allow portal users to login through OpenID Connect Provider",
    "version": "16.0.1.0.0",
    "author": ("CRogos (glueckkanja AG), Odoo Community Association (OCA)"),
    "license": "AGPL-3",
    "maintainers": ["CRogos"],
    "category": "hr",
    "website": "https://github.com/OCA/server-auth",
    "depends": ["auth_oauth", "portal"],
    "data": [
        "wizard/portal_wizard_views.xml",
    ],
    "auto_install": False,
    "installable": True,
}
