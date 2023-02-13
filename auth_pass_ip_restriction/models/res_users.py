from odoo import _, models
from odoo.exceptions import AccessDenied
from odoo.http import request
from odoo.tools.config import config


class ResUsers(models.Model):
    _inherit = "res.users"

    def _check_credentials(self, password, env):
        ignored_endpoints = config.get("auth_pass_ignored_endpoints")
        if (
            not request
            or (ignored_endpoints and request.httprequest.path in ignored_endpoints)
            or env.get("bypass_ip_check")
        ):
            return super()._check_credentials(password, env)
        ip = request.httprequest.environ["REMOTE_ADDR"]
        ip_whitelist = config.get("auth_pass_ip_whitelist", ["127.0.0.1"])
        if ip_whitelist and ip not in ip_whitelist:
            raise AccessDenied(_("Password authentication is disabled for IP %s") % ip)
        return super()._check_credentials(password, env)
