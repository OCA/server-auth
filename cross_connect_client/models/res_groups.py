# Copyright 2024 Akretion (http://www.akretion.com).
# @author Florian Mounier <florian.mounier@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResGroups(models.Model):
    _inherit = "res.groups"

    cross_connect_server_id = fields.Many2one(
        "cross.connect.server", string="Originating Cross Connect Server"
    )
    cross_connect_server_group_id = fields.Integer(
        string="Originating Cross Connect Server Group ID"
    )

    _sql_constraints = [
        (
            "cross_connect_server_group_id_cross_connect_server_id_unique",
            "unique (cross_connect_server_group_id, cross_connect_server_id)",
            "Cross Connect Server Group ID must be unique per Cross Connect Server",
        )
    ]
