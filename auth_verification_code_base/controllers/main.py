# Copyright 2022 Akretion
# Copyright 2022 Toodigit
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging

from odoo import SUPERUSER_ID, _, api, http, registry
from odoo.exceptions import AccessDenied
from odoo.http import local_redirect, request
from odoo.service.security import compute_session_token

from odoo.addons.web.controllers.main import Home, ensure_db

from ..common import DEFAULT_MAX_VERIF_CODE_GEN_DELAY, TooManyVerifResendExc

_logger = logging.getLogger(__name__)
REF_VERIFICATION_SCREEN = "auth_verification_code_base.verification_screen"
SESSION_PARAMS = ["db", "uid", "login", "context", "debug"]


def redirect_to_code_page(info=None):
    return local_redirect("/web/verification/login", info or {})


def redirect_to_resend_page(info=None):
    return local_redirect("/web/verification/resend", info or {})


def push_session():
    stored_session_info = {}
    for el in SESSION_PARAMS:
        stored_session_info[el] = request.session.get(el)
        setattr(request.session, el, None)
    request.session.context = {}
    request.session.debug = ""
    request.session.stored_session_info = stored_session_info


def pop_session():
    for k, v in request.session.stored_session_info.items():
        setattr(request.session, k, v)
    request.session.session_token = compute_session_token(
        request.session, api.Environment(request.cr, SUPERUSER_ID, {})
    )


class VerifCodeLogin(Home):
    def _find_code_from_session_token(self):
        token = request.session.auth_verification_token
        env = api.Environment(request.cr, SUPERUSER_ID, {})
        verification_code = env["auth.verification.code"].search(
            [("token", "=", token)]
        )
        if not verification_code:
            raise  # This should never happen
        return verification_code

    def _verify_auth_code(self, *args, **kw):
        code_number = args[1].get("verification_code")
        verification_code = self._find_code_from_session_token()
        return verification_code.verify(code_number)

    def _check_use_verification_code(self):
        env = api.Environment(request.cr, SUPERUSER_ID, {})
        activate_code_auth = env["ir.config_parameter"].get_param(
            "activate_verification_code"
        )
        return bool(activate_code_auth)

    @http.route("/web/verification/resend", auth="public")
    def web_verification_code_resend(self, *args, **kw):
        token = request.session.auth_verification_token
        if token:
            try:
                with registry(request.session.db).cursor() as cr:
                    env = api.Environment(cr, SUPERUSER_ID, {})
                    token = (
                        env["auth.verification.code"]
                        .search([("token", "=", token)])
                        .user_id.generate_verification_code()
                    )
                    request.session.auth_verification_token = token
                    return redirect_to_code_page({"resend": True})
            except TooManyVerifResendExc:
                return redirect_to_code_page({"codesexc": True})
        else:
            # This should never happen
            push_session()
            raise AccessDenied

    @http.route("/web/verification/login", auth="public", website=True)
    def web_verification_code_login(self, *args, **kw):
        token = request.session.auth_verification_token
        if not token:
            raise
        code = self._find_code_from_session_token()
        if code.check_expired():
            request.session.try_resend_from_expired = True
            return redirect_to_resend_page()
        if request.httprequest.method == "GET":
            vals = {}
            resend_mode = getattr(request.session, "try_resend_from_expired", False)
            if kw.get("resend"):
                if resend_mode:
                    vals["error"] = _("Your code is expired, a new code has been sent")
                else:
                    vals["message"] = _("A new verification code has been sent")
            if kw.get("codesexc"):
                if resend_mode:
                    vals["error"] = _(
                        "Your code is expired and"
                        " too many verification codes have been requested,"
                        " try again later ({} minutes)".format(
                            self._get_param_max_verif_code_generation()
                        )
                    )
                else:
                    vals["error"] = _(
                        "Too many verification codes requested, "
                        "try again later ({} minutes)".format(
                            self._get_param_max_verif_code_generation()
                        )
                    )
            return request.render(REF_VERIFICATION_SCREEN, vals)
        if request.httprequest.method == "POST":
            error, user = self._verify_auth_code(args, kw)
            if error:
                response = request.render(REF_VERIFICATION_SCREEN, {"error": error},)
                response.headers["X-Frame-Options"] = "DENY"
                return response
            else:
                request.session.auth_verification_token = False
                pop_session()
                return http.redirect_with_hash(self._login_redirect(user))

    def _get_auth_verif_token(self):
        with registry(request.session.db).cursor() as cr:
            env = api.Environment(cr, SUPERUSER_ID, {})
            uid = env["res.users"].authenticate(
                request.session.db,
                request.params["login"],
                request.params["password"],
                env,
            )
            if not uid:
                raise AccessDenied
            user = env["res.users"].browse(uid)
            return user.get_verification_code_token()

    def _get_param_max_verif_code_generation(self):
        with registry(request.session.db).cursor() as cr:
            env = api.Environment(cr, SUPERUSER_ID, {})
            return int(
                env["ir.config_parameter"].get_param(
                    "max_verif_code_generation",
                    default=DEFAULT_MAX_VERIF_CODE_GEN_DELAY,
                )
            )

    @http.route()
    def web_login(self, *args, **kw):
        ensure_db()
        # compatibility with website module
        request.params["login_success"] = False
        if not self._check_use_verification_code():
            return super().web_login(*args, **kw)

        values = {}
        if request.httprequest.method == "GET":
            if request.session.auth_verification_token:
                response = redirect_to_code_page()
            else:
                response = super().web_login(*args, **kw)
        elif request.httprequest.method == "POST":
            try:
                token = self._get_auth_verif_token()
                if token:
                    super().web_login(*args, **kw)
                    push_session()
                    request.session.auth_verification_token = token
                    response = redirect_to_code_page()
                else:  # verification is confirmed
                    return super().web_login(*args, **kw)
            except AccessDenied as e:
                if e.args == AccessDenied().args:
                    values["error"] = _("Wrong login/password")
                else:
                    values["error"] = e.args[0]
                response = request.render("web.login", values)
            except TooManyVerifResendExc:
                values["error"] = _(
                    "A new verification code is required, "
                    "but you have already generated too many. "
                    "Please try again later ({} minutes).".format(
                        self._get_param_max_verif_code_generation()
                    )
                )
                response = request.render("web.login", values)
        else:
            if "error" in request.params and request.params.get("error") == "access":
                values["error"] = _(
                    "Only employee can access this database. Please contact the administrator."
                )
                response = request.render("web.login", values)
        return response
