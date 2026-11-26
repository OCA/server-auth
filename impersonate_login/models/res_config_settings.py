from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    restrict_impersonate_admin_settings = fields.Boolean(
        string="Restrict Impersonation of 'Administration: Settings' Users",
        config_parameter="impersonate_login.restrict_impersonate_admin_settings",
        help=(
            "If enabled, users with the 'Administration: Settings' access right"
            " cannot be impersonated."
        ),
        default=False,
    )

    def set_values(self):
        res = super().set_values()
        # Whether a user can be impersonated depends on this setting.
        self.env["res.users"].invalidate_model(["impersonate_allowed"])
        return res
