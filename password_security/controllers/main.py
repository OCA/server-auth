# Copyright 2015 LasLabs Inc.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

import operator

from odoo import http
from odoo.exceptions import UserError
from odoo.http import request

from odoo.addons.auth_signup.controllers.main import AuthSignupHome
from odoo.addons.web.controllers.main import Session


class PasswordSecuritySession(Session):
    @http.route()
    def change_password(self, fields):
        new_password = operator.itemgetter("new_password")(
            dict(list(map(operator.itemgetter("name", "value"), fields)))
        )
        user_id = request.env.user
        user_id._check_password(new_password)
        return super(PasswordSecuritySession, self).change_password(fields)


class PasswordSecurityHome(AuthSignupHome):
    def do_signup(self, qcontext):
        password = qcontext.get("password")
        user_id = request.env.user
        user_id._check_password(password)
        return super(PasswordSecurityHome, self).do_signup(qcontext)

    @http.route("/password_security/estimate", auth="none", type="json")
    def estimate(self, password):
        return request.env["res.users"].get_estimation(password)

    def _login_redirect(self, uid, redirect=None):
        res = super()._login_redirect(uid, redirect=redirect)
        if (
            request.session.uid and request.env.user._password_has_expired()
        ):  # fully logged but password expired
            # My password is expired, kick me out
            request.env.user.action_expire_password()
            request.session.logout(keep_db=True)
            # I was kicked out, so set login_success in request params to False
            request.params["login_success"] = False
            res = request.env.user.partner_id.signup_url
        return res

    def get_auth_signup_config(self):
        signup_config = super().get_auth_signup_config()
        for property_name in (
            "password_length",
            "password_lower",
            "password_upper",
            "password_numeric",
            "password_special",
            "password_estimate",
        ):
            signup_config[property_name] = request.env.company[property_name]
        return signup_config

    @http.route()
    def web_auth_signup(self, *args, **kw):
        try:
            return super(PasswordSecurityHome, self).web_auth_signup(*args, **kw)
        except UserError as e:
            qcontext = self.get_auth_signup_qcontext()
            qcontext["error"] = str(e)
            return request.render("auth_signup.signup", qcontext)
