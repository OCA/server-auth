# Copyright 2026 Trobz
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    auth_api_key_native_generate_duration = fields.Integer(
        string="Generated API Key Validity (days)",
        default=90,
        config_parameter="auth_api_key_native_generate.duration",
        help="Validity window, in days, applied to API keys issued through the "
        "/api/auth/generate_api_key endpoint. Only newly generated keys are "
        "affected; existing keys keep their own expiration date.",
    )
