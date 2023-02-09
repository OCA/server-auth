# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


import werkzeug.utils

from odoo import _, http
from odoo.exceptions import AccessDenied
from odoo.http import request

from odoo.addons.portal.controllers.web import Home
from odoo.addons.web.controllers.main import ensure_db, login_and_redirect


class DeviceController(Home):
    @http.route()
    def web_login(self, *args, **kw):
        ensure_db()
        if (
            request.httprequest.method == "GET"
            and request.session.uid
            and request.params.get("redirect")
        ):
            # Redirect if already logged in and redirect param is present
            return http.redirect_with_hash(request.params.get("redirect"))

        response = super().web_login(*args, **kw)
        if response.is_qweb:
            error = request.params.get("auth_device_error")
            if error == "1":
                error = _("Access Denied")
            elif error == "2":
                error = _("Missing Device Code")
            elif error == "3":
                error = _("Internal Error")
            else:
                error = None
            if error:
                response.qcontext["error"] = error

        return response


class AuthDeviceController(http.Controller):
    @http.route("/auth_device/login", type="http", auth="none")
    def device_login(self, redirect="/web", **kw):
        ensure_db()
        if request.httprequest.method == "GET" or request.session.uid:
            return werkzeug.utils.redirect(redirect)
        # By default redirect to Access denied Error
        url = "/web/login?auth_device_error=1"
        # If no Device Code redirect to Missing Device Code Error
        if not request.params.get("device_code", None):
            return werkzeug.utils.redirect("/web/login?auth_device_error=2", 303)
        user = (
            request.env["res.users"]
            .sudo()
            .search(
                [
                    ("device_code", "=", request.params["device_code"]),
                    ("is_allowed_to_connect_with_device", "=", True),
                ]
            )
        )
        if not user:
            # If no user found redirect to Access Denied
            url = "/web/login?auth_device_error=1"
        elif len(user) > 1:
            # Elif more than one user found redirect to Internal Error
            url = "/web/login?auth_device_error=3"
        elif user and request.httprequest.method == "POST":
            try:
                return login_and_redirect(
                    db=request.session.db,
                    login=user.login,
                    key=request.params["device_code"],
                    redirect_url=redirect,
                )
            except AccessDenied:
                url = "/web/login?auth_device_error=1"
        return werkzeug.utils.redirect(url, 303)
