# Copyright 2015 Antiun Ingeniería, S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging

from email_validator import EmailSyntaxError, EmailUndeliverableError, validate_email
from werkzeug.exceptions import NotFound

from odoo.http import request, route

from odoo.addons.auth_signup.controllers.main import AuthSignupHome

_logger = logging.getLogger(__name__)


class SignupVerifyEmail(AuthSignupHome):
    @route()
    def web_auth_signup(self, *args, **kw):
        if request.params.get("login") and not request.params.get("password"):
            return self.passwordless_signup()
        return super().web_auth_signup(*args, **kw)

    def passwordless_signup(self):
        qcontext = self.get_auth_signup_qcontext()

        # Same guards as core's web_auth_signup
        if not qcontext.get("token") and not qcontext.get("signup_enabled"):
            raise NotFound()
        if qcontext.get("error"):
            return request.render("auth_signup.signup", qcontext)

        login = request.params.get("login", "")

        # Check good format of e-mail
        try:
            validate_email(login)
        except EmailSyntaxError as error:
            qcontext["error"] = getattr(
                error,
                "message",
                self.env._("That does not seem to be an email address."),
            )
            return request.render("auth_signup.signup", qcontext)
        except EmailUndeliverableError as error:
            qcontext["error"] = str(error)
            return request.render("auth_signup.signup", qcontext)
        except Exception as error:
            qcontext["error"] = str(error)
            return request.render("auth_signup.signup", qcontext)

        # Only pass the fields the signup form is meant to set: request
        # params go to a sudo copy() of the template user
        values = {
            "login": login,
            "name": request.params.get("name"),
            "email": request.params.get("email") or login,
            "password": "",
        }
        # Same language handling as core's _prepare_signup_values
        lang = request.env.context.get("lang")
        if lang in dict(request.env["res.lang"].get_installed()):
            values["lang"] = lang
        sudo_users = request.env["res.users"].with_context(create_user=True).sudo()

        try:
            with request.env.cr.savepoint():
                sudo_users.signup(values, qcontext.get("token"))
                sudo_users.reset_password(login)
        except Exception:
            # Duplicate key or wrong SMTP settings, probably
            _logger.exception("Passwordless signup failed")
            if request.env["res.users"].sudo().search([("login", "=", login)]):
                qcontext["error"] = self.env._(
                    "Another user is already registered using this email address."
                )
            else:
                # Agnostic message for security
                qcontext["error"] = self.env._(
                    "Something went wrong, please try again later or contact us."
                )
            return request.render("auth_signup.signup", qcontext)

        qcontext["message"] = self.env._("Check your email to activate your account!")
        return request.render("auth_signup.reset_password", qcontext)
