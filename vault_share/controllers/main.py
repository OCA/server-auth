# © 2021 Florian Kantelberg - initOS GmbH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import _, http
from odoo.http import request

_logger = logging.getLogger(__name__)


class Controller(http.Controller):
    @http.route("/vault/share/<string:token>", type="http", auth="public")
    def vault_share(self, token):
        ctx = {"disable_footer": True, "token": token}
        share = request.env["vault.share"].sudo()
        secret = share.get(token, ip=request.httprequest.remote_addr)
        if secret is None:
            ctx["error"] = _("The secret expired")
            return request.render("vault_share.share", ctx)

        if len(secret) != 1:
            ctx["error"] = _("Invalid token")
            return request.render("vault_share.share", ctx)

        ctx.update(
            {
                "encrypted": secret.secret,
                "salt": secret.salt,
                "iv": secret.iv,
                "encrypted_file": secret.secret_file,
                "filename": secret.filename,
            }
        )
        return request.render("vault_share.share", ctx)
