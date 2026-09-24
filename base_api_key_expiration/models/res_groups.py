# Copyright 2026 Camptocamp SA
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class ResGroups(models.Model):
    _inherit = "res.groups"

    api_key_duration = fields.Float(
        string="API Keys maximum duration days",
        help="Determines the maximum duration of an api key created by a user "
        "belonging to this group.",
    )

    _sql_constraints = [
        (
            "check_api_key_duration",
            "CHECK(api_key_duration >= 0)",
            "The api key duration cannot be a negative value.",
        ),
    ]
