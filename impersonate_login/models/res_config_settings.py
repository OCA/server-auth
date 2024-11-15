from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    restrict_impersonate_admin_settings = fields.Boolean(
        string="Restrict Impersonation of 'Administration: Settings' Users",
        config_parameter="impersonate_login.restrict_impersonate_admin_settings",
        help="If enabled, users with the 'Administration: Settings' access right"
        " cannot be impersonated.",
        default=False,
    )
