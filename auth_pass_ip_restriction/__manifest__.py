# Copyright 2023 Therp BV (https://www.therp.nl)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Password Authentication IP Restriction",
    "version": "14.0.1.0.0",
    "summary": "Restricts regular password authentication to a whitelist of IPs",
    "author": "Therp BV, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/server-auth",
    "license": "AGPL-3",
    "category": "Uncategorized",
    "sequence": 0,
    "depends": [
        "auth_signup",
        "web",
    ],
    "data": [
        "views/webclient_templates.xml",
    ],
    "application": False,
    "installable": True,
}
