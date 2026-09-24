# Copyright 2026 Camptocamp SA
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import http
from odoo.http import request

from odoo.addons.auth_totp.controllers.home import TRUSTED_DEVICE_COOKIE, Home


class TrustedDeviceAgeHome(Home):
    @http.route()
    def web_totp(self, redirect=None, **kwargs):
        response = super().web_totp(redirect=redirect, **kwargs)
        # the 17.0 controller sets the cookie of a new trusted device for 90
        # days: set it again with the trusted device age, like 19.0
        cookies = response.headers.getlist("Set-Cookie")
        prefix = f"{TRUSTED_DEVICE_COOKIE}="
        device_cookies = [cookie for cookie in cookies if cookie.startswith(prefix)]
        if device_cookies:
            key = device_cookies[-1].split(";", 1)[0][len(prefix) :]
            response.headers.remove("Set-Cookie")
            for cookie in cookies:
                if cookie not in device_cookies:
                    response.headers.add("Set-Cookie", cookie)
            response.set_cookie(
                key=TRUSTED_DEVICE_COOKIE,
                value=key,
                max_age=request.env["auth_totp.device"]._get_trusted_device_age(),
                httponly=True,
                samesite="Lax",
            )
        return response
