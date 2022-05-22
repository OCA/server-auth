# © 2021 Florian Kantelberg - initOS GmbH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import _, http
from odoo.http import request

_logger = logging.getLogger(__name__)


class Controller(http.Controller):
    @http.route("/vault/inbox/<string:token>", type="http", auth="public")
    def vault_inbox(self, token):
        ctx = {"disable_footer": True, "token": token}
        # Find the right token
        inbox = request.env["vault.inbox"].sudo().find_inbox(token)
        user = request.env["res.users"].sudo().find_user_of_inbox(token)
        _logger.info("%s: %s", inbox, user)
        if len(inbox) == 1 and inbox.accesses > 0:
            ctx.update({"name": inbox.name, "public": inbox.user_id.active_key.public})
        elif len(inbox) == 0 and len(user) == 1:
            ctx["public"] = user.active_key.public

        # A valid token would mean we found a public key
        if not ctx.get("public"):
            ctx["error"] = _("Invalid token")
            return request.render("vault.inbox", ctx)

        # Just render if GET method
        if request.httprequest.method != "POST":
            return request.render("vault.inbox", ctx)

        # Check the param
        name = request.params.get("name")
        secret = request.params.get("encrypted")
        secret_file = request.params.get("encrypted_file")
        filename = request.params.get("filename")
        iv = request.params.get("iv")
        key = request.params.get("key")
        if not name:
            ctx["error"] = _("Please specify a name")
            return request.render("vault.inbox", ctx)

        if not secret and not secret_file:
            ctx["error"] = _("No secret found")
            return request.render("vault.inbox", ctx)

        if secret_file and not filename:
            ctx["error"] = _("Missing filename")
            return request.render("vault.inbox", ctx)

        if not iv or not key:
            ctx["error"] = _("Something went wrong with the encryption")
            return request.render("vault.inbox", ctx)

        try:
            inbox.store_in_inbox(name, secret, secret_file, iv, key, user, filename)
        except Exception as e:
            _logger.exception(e)
            ctx["error"] = _(
                "An error occured. Please contact the user or administrator"
            )
            return request.render("vault.inbox", ctx)

        ctx["message"] = _("Successfully stored")
        return request.render("vault.inbox", ctx)

    @http.route("/vault/public", type="json")
    def vault_public(self, user_id):
        """ Get the public key of a specific user """
        user = request.env["res.users"].sudo().browse(user_id).exists()
        if not user or not user.keys:
            return {}

        return {"public_key": user.active_keys.public}

    @http.route("/vault/keys/store", auth="user", type="json")
    def vault_store_keys(self, **kwargs):
        """ Store the key pair for the current user """
        return request.env["res.users.key"].store(**kwargs)

    @http.route("/vault/keys/get", auth="user", type="json")
    def vault_get_keys(self):
        """ Get the currently active key pair """
        return request.env.user.get_vault_keys()

    @http.route("/vault/rights/get", auth="user", type="json")
    def vault_get_right_keys(self):
        """ Get the master keys from the vault.right records """
        rights = request.env.user.vault_right_ids
        return {right.vault_id.uuid: right.key for right in rights}

    @http.route("/vault/rights/store", auth="user", type="json")
    def vault_store_right_keys(self, keys):
        """ Store the master keys to the specific vault.right records """
        if not isinstance(keys, dict):
            return

        for right in request.env.user.vault_right_ids:
            master_key = keys.get(right.vault_id.uuid)

            if isinstance(master_key, str):
                right.key = master_key
