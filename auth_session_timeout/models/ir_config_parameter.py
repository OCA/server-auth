# (c) 2015 ACSONE SA/NV, Dhinesh D
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, models

DELAY_KEY = "inactive_session_time_out_delay"
IGNORED_PATH_KEY = "inactive_session_time_out_ignored_url"


class IrConfigParameter(models.Model):
    _inherit = "ir.config_parameter"

    @api.model
    def _auth_timeout_get_parameter_delay(self):
        return int(
            self.env["ir.config_parameter"]
            .sudo()
            .get_param(
                DELAY_KEY,
                7200,
            )
        )

    @api.model
    def _auth_timeout_get_parameter_ignored_urls(self):
        urls = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param(
                IGNORED_PATH_KEY,
                "",
            )
        )
        return urls.split(",")

    def write(self, vals):
        res = super().write(vals)
        self.env.registry.clear_cache()
        self._auth_timeout_get_parameter_delay()
        self.env.registry.clear_cache()
        self._auth_timeout_get_parameter_ignored_urls()
        return res
