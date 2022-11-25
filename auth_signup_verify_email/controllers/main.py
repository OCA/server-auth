# Copyright 2015 Antiun Ingeniería, S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging

from email_validator import EmailSyntaxError, EmailUndeliverableError, validate_email

from odoo import _
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
        values = request.params
        qcontext = self.get_auth_signup_qcontext()

        # Check good format of e-mail
        try:
            validate_email(values.get("login", ""))
        except EmailSyntaxError as error:
            qcontext["error"] = getattr(
                error,
                "message",
                _("That does not seem to be an email address."),
            )
            return request.render("auth_signup.signup", qcontext)
        except EmailUndeliverableError as error:
            qcontext["error"] = str(error)
            return request.render("auth_signup.signup", qcontext)
        except Exception as error:
            qcontext["error"] = str(error)
            return request.render("auth_signup.signup", qcontext)
        if not values.get("email"):
            values["email"] = values.get("login")

        # remove values that could raise "Invalid field '*' on model 'res.users'"
        values.pop("redirect", "")
        values.pop("token", "")

        # Remove password
        values["password"] = ""
        sudo_users = request.env["res.users"].with_context(create_user=True).sudo()

        try:
            with request.cr.savepoint():
                sudo_users.signup(values, qcontext.get("token"))
                sudo_users.reset_password(values.get("login"))
        except Exception as error:
            # Duplicate key or wrong SMTP settings, probably
            _logger.exception(error)
            if (
                request.env["res.users"]
                .sudo()
                .search([("login", "=", qcontext.get("login"))])
            ):
                qcontext["error"] = _(
                    "Another user is already registered using this email" " address."
                )
            else:
                # Agnostic message for security
                qcontext["error"] = _(
                    "Something went wrong, please try again later or" " contact us."
                )
            return request.render("auth_signup.signup", qcontext)

        qcontext["message"] = _("Check your email to activate your account!")
        return request.render("auth_signup.reset_password", qcontext)
