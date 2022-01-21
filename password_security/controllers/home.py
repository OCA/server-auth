# Copyright 2022 brain-tec AG (https://bt-group.com)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import http
from odoo.http import request

from odoo.addons.auth_totp.controllers.home import Home


class PasswordSecurity2FAHome(Home):
    @http.route()
    def web_totp(self, redirect=None, **kwargs):
        already_logged_in = request.session.uid
        result = super(PasswordSecurity2FAHome, self).web_totp(redirect, **kwargs)

        if already_logged_in or not (
            request.session.uid and request.env.user._password_has_expired()
        ):
            return result

        # My password is expired, kick me out
        request.env.user.action_expire_password()
        request.session.logout(keep_db=True)
        redirect = request.env.user.partner_id.signup_url
        return http.redirect_with_hash(redirect)
