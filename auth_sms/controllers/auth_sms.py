# Copyright 2019 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
import base64
import random

from odoo import _, http
from odoo.http import request

from odoo.addons.web.controllers.home import Home

from ..exceptions import (
    AccessDeniedNoSmsCode,
    AccessDeniedSmsRateLimit,
    AccessDeniedWrongSmsCode,
)


class AuthSms(Home):
    @http.route()
    def web_login(self, redirect=None, **kw):
        try:
            return super().web_login(redirect=redirect, **kw)
        except AccessDeniedNoSmsCode as exception:
            try:
                request.env["res.users"]._auth_sms_send(exception.user.id)
            except AccessDeniedSmsRateLimit:
                return self._show_rate_limit(redirect=None, **kw)
            return self._show_sms_entry(redirect=None, **kw)

    def _show_rate_limit(self, redirect=None, **kw):
        """User has requested to much sms codes in a short period."""
        # providers here as elsewhere are included in case auth_oauth is installed.
        return request.render(
            "web.login",
            dict(
                request.params.copy(),
                providers=[],
                error=_("Rate limit for SMS exceeded"),
            ),
        )

    def _show_sms_entry(self, redirect=None, **kw):
        """Show copy of login screen for sms entry."""
        # password will be stored, encrypted, in the session, while
        # the secret will be send (and later retrieved) from the browser.
        password_bytes = request.params["password"].encode("utf8")
        secret = self._auth_sms_generate_secret()
        encrypted_password = self._auth_sms_xor(password_bytes, secret)
        request.session["auth_sms.password"] = encrypted_password
        encoded_secret_string = base64.b64encode(secret).decode("utf8")
        return request.render(
            "auth_sms.template_code",
            dict(
                request.params.copy(),
                secret=encoded_secret_string,
                redirect=redirect,
                providers=[],
                message=_("Please fill in the code sent to you by SMS"),
                **kw
            ),
        )

    @http.route("/auth_sms/code", auth="none")
    def code(self, password=None, secret=None, redirect=None, **kw):
        # IN this case the password argument really contains the sms code.
        request.session["auth_sms.code"] = password
        encrypted_password = request.session["auth_sms.password"]
        decoded_secret_bytes = base64.b64decode((secret or "").encode("utf8"))
        decrypted_password = self._auth_sms_xor(
            encrypted_password, decoded_secret_bytes
        )
        request.params["password"] = decrypted_password.decode("utf8")
        request.params["login"] = request.params["user_login"]
        try:
            return self.web_login(
                redirect=redirect, **dict(kw, password=request.params["password"])
            )
        except AccessDeniedWrongSmsCode:
            return self._show_wrong_sms_code(secret, redirect=None, **kw)

    def _show_wrong_sms_code(self, secret, redirect=None, **kw):
        """Wrong sms code entered, user can try again."""
        del request.session["auth_sms.code"]
        return request.render(
            "auth_sms.template_code",
            dict(
                request.params.copy(),
                secret=secret,
                providers=[],
                redirect=redirect,
                databases=[],
                error=_("Could not verify code"),
                **kw
            ),
        )

    def _auth_sms_generate_secret(self):
        """Generate an OTP for storing the password in the session."""
        otp_size = int(
            request.env["ir.config_parameter"]
            .sudo()
            .get_param(
                "auth_sms.otp_size",
                128,
            )
        )
        return bytes(bytearray([random.randrange(256) for dummy in range(otp_size)]))

    def _auth_sms_xor(self, password, secret):
        """Xor password with secret, to encrypt or decrypt password.

        password and secret should both be byte strings.
        """
        assert len(secret) >= len(password)
        assert isinstance(password, bytes)
        assert isinstance(secret, bytes)
        return bytes(bytearray(c ^ otp for c, otp in zip(password, secret)))
