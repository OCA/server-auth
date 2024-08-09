# Copyright 2019 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
import base64
import itertools
import random

from odoo import _, http
from odoo.http import request

from odoo.addons.web.controllers.main import Home

from ..exceptions import (
    AccessDeniedNoSmsCode,
    AccessDeniedSmsRateLimit,
    AccessDeniedWrongSmsCode,
)


class AuthSms(Home):
    @http.route()
    def web_login(self, redirect=None, **kw):
        try:
            return super(AuthSms, self).web_login(redirect=redirect, **kw)
        except AccessDeniedNoSmsCode as exception:
            try:
                request.env["res.users"].sudo()._auth_sms_send(exception.user.id)
            except AccessDeniedSmsRateLimit:
                return request.render(
                    "web.login",
                    dict(
                        request.params.copy(),
                        error=_("Rate limit for SMS exceeded"),
                    ),
                )
            secret = self._auth_sms_generate_secret()
            request.session["auth_sms.password"] = self._auth_sms_xor(
                request.params["password"],
                secret,
            )
            return request.render(
                "auth_sms.template_code",
                dict(
                    request.params.copy(),
                    secret=base64.b64encode(secret),
                    redirect=redirect,
                    message=_("Please fill in the code sent to you by SMS"),
                    **kw
                ),
            )

    @http.route("/auth_sms/code", auth="none")
    def code(self, password=None, secret=None, redirect=None, **kw):
        request.session["auth_sms.code"] = password
        try:
            request.params["password"] = bytearray(
                b
                for b in self._auth_sms_xor(
                    request.session["auth_sms.password"] or bytearray(),
                    bytearray(base64.b64decode(secret or "")),
                    decode_input=False,
                    pad=False,
                )
                # as we pad the password with null bytes, remove them here
                if b
            ).decode("utf8")
            request.params["login"] = request.params["user_login"]
            return self.web_login(
                redirect=redirect, **dict(kw, password=request.params["password"])
            )
        except AccessDeniedWrongSmsCode:
            del request.session["auth_sms.code"]
            return request.render(
                "auth_sms.template_code",
                dict(
                    request.params.copy(),
                    secret=secret,
                    redirect=redirect,
                    databases=[],
                    error=_("Could not verify code"),
                    **kw
                ),
            )

    def _auth_sms_generate_secret(self):
        """generate an OTP for storing the password in the session"""
        return bytearray(
            [
                random.randrange(256)
                for dummy in range(
                    int(
                        request.env["ir.config_parameter"]
                        .sudo()
                        .get_param(
                            "auth_sms.otp_size",
                            128,
                        )
                    )
                )
            ]
        )

    def _auth_sms_xor(self, input_string, secret, decode_input=True, pad=True):
        """xor input string with a pregenerated OTP, pad with 0"""
        input_bytes = (
            decode_input and bytearray(input_string, encoding="utf8") or input_string
        )
        return bytearray(
            c ^ otp
            for c, otp in itertools.izip(
                itertools.chain(
                    input_bytes,
                    pad
                    and itertools.repeat(
                        0,
                        len(secret) - len(input_bytes) % (len(secret) or 1),
                    )
                    or [],
                ),
                itertools.cycle(secret),
            )
        )
