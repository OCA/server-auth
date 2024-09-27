# Copyright 2024 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
{
    "name": "Empty users password",
    "summary": "Allows to empty password of users",
    "version": "18.0.1.0.0",
    "development_status": "Beta",
    "category": "Uncategorized",
    "website": "https://github.com/OCA/server-auth",
    "author": "Camptocamp, Odoo Community Association (OCA)",
    "maintainers": ["grindtildeath"],
    "license": "AGPL-3",
    "depends": [
        "base",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/res_users.xml",
        "wizard/empty_password.xml",
    ],
}
