# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import models
from odoo.http import request


class IrHttp(models.AbstractModel):
    _inherit = "ir.http"

    @classmethod
    def _authenticate(cls, endpoint):
        res = super()._authenticate(endpoint=endpoint)
        if request and request.session and request.session.uid:
            # The user is read below, before core _pre_dispatch replaces an
            # inactive context language: Environment.lang would raise and the
            # request would end in "400 Invalid language code".
            lang = request.env.context.get("lang")
            if lang and not request.env["res.lang"]._get_data(code=lang):
                request.update_context(lang=None)
            if not request.env["res.users"].browse(request.session.uid)._is_public():
                request.env.user._auth_timeout_check()
        return res
