# SPDX-FileCopyrightText: 2025 Coop IT Easy SC
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from odoo import _, http
from odoo.http import request

from odoo.addons.auth_signup.controllers.main import AuthSignupHome

PARAMS_ERROR_KEY = "_signup_recaptcha_v2_error_msg"


class AuthSignupRecaptchaV2(AuthSignupHome):
    def get_auth_signup_qcontext(self):
        qcontext = super().get_auth_signup_qcontext()
        # get error from params if any (see web_auth_signup())
        if PARAMS_ERROR_KEY in request.params:
            qcontext["error"] = request.params[PARAMS_ERROR_KEY]
        return qcontext

    @http.route()
    def web_auth_signup(self, *args, **kwargs):
        # Validate the recaptcha
        if request.httprequest.method == "POST":
            result, error_msg = request.website.is_recaptcha_v2_valid(kwargs)
            # Add error to params in order to get accessible from
            # get_auth_signup_qcontetx method.
            if not result:
                request.params[PARAMS_ERROR_KEY] = _(
                    "Error validating the CAPTCHA: {0}"
                ).format(error_msg)
        response = super().web_auth_signup(*args, **kwargs)
        return response
