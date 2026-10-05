# Copyright 2022 brain-tec AG (https://bt-group.com)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import http
from odoo.http import request
from odoo.http.session import logout

from odoo.addons.auth_totp.controllers.home import Home


class PasswordSecurity2FAHome(Home):
    @http.route()
    def web_totp(self, redirect=None, **kwargs):
        already_logged_in = request.session.uid
        result = super().web_totp(redirect, **kwargs)
        if already_logged_in or not (
            request.session.uid and request.env.user._password_has_expired()
        ):
            return result
        # Password expired: force a proper logout.
        # `Session` has NO `logout` method in Odoo 20 — `logout` is a
        # module-level function in `odoo.http.session` that clears the session
        # and flags it for rotation. The previous `request.session.logout(...)`
        # call raised AttributeError which, if swallowed upstream, left the
        # user authenticated with a stale session_token (session bleed).
        request.env.user.action_expire_password()
        logout(request.session, keep_db=True)
        request.params["login_success"] = False
        redirect = request.env.user.partner_id._get_signup_url()
        return request.redirect(redirect)
