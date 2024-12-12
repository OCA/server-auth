# Copyright 2024 Akretion (http://www.akretion.com).
# @author Florian Mounier <florian.mounier@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResUsers(models.Model):
    _inherit = "res.users"

    cross_connect_client_id = fields.Many2one(
        "cross.connect.client",
        string="Cross Connect Client",
        help="The cross connect client that created this user.",
    )
    cross_connect_client_user_id = fields.Integer(
        string="Cross Connect Client User ID",
        help="The user ID on the cross connect client.",
    )
