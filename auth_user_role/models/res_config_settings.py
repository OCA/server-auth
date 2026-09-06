# Copyright 2026 360ERP (<https://www.360erp.com>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    auth_user_role_strict_sync = fields.Boolean(
        string="Strict Identity Role Synchronization",
        config_parameter="auth_user_role.strict_sync",
        default=True,
        help=(
            "If enabled globally, any Odoo roles manually assigned to a user will be "
            "removed if they are not explicitly provided by the "
            "Identity Provider payload."
        ),
    )
