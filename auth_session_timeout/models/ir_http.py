# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import models
from odoo.http import request


class IrHttp(models.AbstractModel):

    _inherit = "ir.http"

    @classmethod
    def _authenticate(cls, endpoint):
        res = super(IrHttp, cls)._authenticate(endpoint=endpoint)
        auth_method = endpoint.routing["auth"]
        if auth_method == "user" and request and request.env and request.env.user:
            request.env.user._auth_timeout_check()
        return res
