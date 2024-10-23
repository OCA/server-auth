# (c) 2015 ACSONE SA/NV, Dhinesh D
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, models, tools

DELAY_KEY = "inactive_session_time_out_delay"
IGNORED_PATH_KEY = "inactive_session_time_out_ignored_url"


class IrConfigParameter(models.Model):
    _inherit = "ir.config_parameter"

    @api.model
    @tools.ormcache("self.env.cr.dbname")
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
    @tools.ormcache("self.env.cr.dbname")
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
        if DELAY_KEY == self.key or IGNORED_PATH_KEY == self.key:
            self.env.registry.clear_cache()
        return res
