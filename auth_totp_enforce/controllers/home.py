# Copyright 2026 ForgeFlow S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, http
from odoo.http import request

import odoo.addons.auth_totp.controllers.home

SESSION_KEY = "totp_enforce_setup"


class Home(odoo.addons.auth_totp.controllers.home.Home):
    @http.route(
        "/web/login/totp/setup",
        type="http",
        auth="public",
        methods=["GET", "POST"],
        sitemap=False,
        website=True,
        multilang=False,
    )
    def web_totp_setup(self, redirect=None, **kwargs):
        if request.session.uid:
            return request.redirect(
                self._login_redirect(request.session.uid, redirect=redirect)
            )
        if not request.session.pre_uid:
            return request.redirect("/web/login")
        user = request.env["res.users"].sudo().browse(request.session.pre_uid)
        if not user._mfa_enforced() or user.totp_enabled:
            return request.redirect("/web/login/totp")
        stored = request.session.get(SESSION_KEY)
        if not stored or stored.get("uid") != user.id:
            secret = user._generate_totp_setup_secret()
            request.session[SESSION_KEY] = {"uid": user.id, "secret": secret}
        else:
            secret = stored["secret"]
        error = None
        if request.httprequest.method == "POST" and kwargs.get("totp_token"):
            if user._totp_enforce_setup(secret, kwargs["totp_token"]):
                request.session.pop(SESSION_KEY, None)
                # Persist secret, session stays partial and delegate to standard MFA
                request.env.flush_all()
                user.invalidate_recordset(["totp_secret", "totp_enabled"])
                request.session.touch()
                return request.redirect(
                    self._login_redirect(user.id, redirect=redirect)
                )
            error = _("Verification failed, please double-check the 6-digit code")
        wizard = (
            request.env["auth_totp.wizard"]
            .sudo()
            .new(
                {
                    "user_id": user.id,
                    "secret": secret,
                }
            )
        )
        request.session.touch()
        return request.render(
            "auth_totp_enforce.auth_totp_setup_form",
            {
                "user": user,
                "error": error,
                "redirect": redirect,
                "secret": secret,
                "qrcode": wizard.qrcode,
                "url": wizard.url,
            },
        )
