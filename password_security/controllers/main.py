# Copyright 2015 LasLabs Inc.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

import logging

from werkzeug.exceptions import BadRequest

from odoo import http
from odoo.http import request

from odoo.addons.auth_signup.controllers.main import AuthSignupHome
from odoo.addons.web.controllers.home import ensure_db

_logger = logging.getLogger(__name__)


class PasswordSecurityHome(AuthSignupHome):
    def do_signup(self, qcontext):
        password = qcontext.get("password")
        user = request.env.user
        user._check_password(password)
        return super().do_signup(qcontext)

    @http.route()
    def web_login(self, *args, **kw):
        ensure_db()
        response = super().web_login(*args, **kw)
        if not request.params.get("login_success"):
            return response
        if not request.env.user:
            return response
        # Utilisateur authentifié — avec 2FA, une seconde étape est nécessaire
        if not (request.session.uid and request.env.user._password_has_expired()):
            return response
        # Mot de passe expiré : déconnexion forcée
        request.env.user.action_expire_password()
        request.session.logout(keep_db=True)
        request.params["login_success"] = False
        redirect = request.env.user.partner_id._get_signup_url()
        return request.redirect(redirect)

    @http.route()
    def web_auth_signup(self, *args, **kw):
        """Intercepte toutes les exceptions non gérées par la méthode parente."""

        try:
            qcontext = self.get_auth_signup_qcontext()
        except Exception:
            raise BadRequest from None  # HTTPError: 400 Client Error: BAD REQUEST

        try:
            return super().web_auth_signup(*args, **kw)
        except Exception as e:
            # UserError est déjà géré par la méthode parente web_auth_signup()
            qcontext["error"] = str(e)
            response = request.render("auth_signup.signup", qcontext)
            response.headers["X-Frame-Options"] = "SAMEORIGIN"
            response.headers["Content-Security-Policy"] = "frame-ancestors 'self'"
            return response
