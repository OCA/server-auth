# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging

from odoo import _, http
from odoo.http import request

from odoo.addons.web.controllers.main import Home

_logger = logging.getLogger(__name__)


class AuthPasswordPwnedHome(Home):
    def _auth_signup_is_installed(self):
        return bool(
            request.env["ir.module.module"]
            .sudo()
            .search(
                [("name", "=", "auth_signup"), ("state", "in", ["installed"])], limit=1
            )
        )

    def _reset_password_enabled(self):
        return (
            request.env["ir.config_parameter"]
            .sudo()
            .get_param("auth_signup.reset_password")
            == "True"
        )

    @http.route()
    def web_login(self, *args, **kw):
        pwned = False
        reset_pw_after_validation = False
        if "password" in kw and request.env.user._passwordhasbeenpwned(kw["password"]):
            if self._auth_signup_is_installed():
                if self._reset_password_enabled():
                    # prevent login with a pwned password and force user to reset it
                    kw["password"] = ""
                    request.params["password"] = ""
                    pwned = _(
                        "This password is known by third parties please reset it and"
                        " use a different password."
                    )
                else:
                    # prepare to hint the user to their email
                    # reset the password after it has been validated
                    reset_pw_after_validation = True
                    pwned = _(
                        "This password is known by third parties an email has been"
                        " sent with instructions how to reset it."
                    )

            else:
                # display a login message and tell the user they should contact the admin
                # to start a safe password change procedure
                kw["password"] = ""
                request.params["password"] = ""
                pwned = _(
                    "This password is known by third parties please contact an"
                    " administrator how to get a new one."
                )
        response = super().web_login(*args, **kw)
        if reset_pw_after_validation and request.params.get("login_success"):
            # do not allow user to continue and send them a reset password email
            request.params["login_success"] = False
            request.session.logout(keep_db=True)
            try:
                request.env["res.users"].sudo().reset_password(kw["login"])
            except Exception as e:
                # Log the exception and continue to tell the "user" an email has been sent.
                # reset_password only throws an exception if the login is not correct
                # / not active so this is most likely someone guessing usernames.
                _logger.error(
                    _("Could not reset password for {login}: {exception}").format(
                        login=kw["login"], exception=e
                    )
                )
            # make the response render the login with our error message
            kw["password"] = ""
            request.params["password"] = ""
            response = super().web_login(*args, **kw)
        if pwned:
            response.qcontext["error"] = pwned
        return response
