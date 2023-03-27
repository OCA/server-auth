# Copyright 2023 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    archived_user_disable_auth_api_key = fields.Boolean(
        related="company_id.archived_user_disable_auth_api_key", readonly=False
    )
