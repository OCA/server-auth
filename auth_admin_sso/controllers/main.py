# Copyright 2026 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
import hashlib
import logging
import os
import secrets
import uuid
from urllib.parse import urlencode

import requests
from werkzeug.exceptions import HTTPException, NotFound

from odoo import http
from odoo.http import request
from odoo.tools import config

from odoo.addons.web.controllers.home import Home

_logger = logging.getLogger(__name__)

try:
    from jose import jwt
    from jose.exceptions import JOSEError
except ImportError:  # pragma: no cover
    jwt = None
    _logger.warning(
        "Admin SSO: python-jose library not installed, OIDC login is disabled"
    )

SESSION_KEY = "auth_admin_sso"
TIMEOUT = 10
REFUSED_MESSAGE = "Login refused. Reference: {ref}"
ISSUE_MESSAGE = (
    "There is an issue with the Admin SSO login (auth_admin_sso). "
    "Ask an administrator to check the server logs for reference {ref}."
)

# OpenID Connect discovery documents, by configured issuer.
_discovery_cache = {}
# Provider signing keys, by (jwks_uri, key id). Refetched when an unknown key
# id shows up, because providers rotate their keys.
_jwks_cache = {}


class SSOError(Exception):
    """Refuse a login. The message is logged, never shown to the browser."""


# A plain class, not a Controller, so it adds no route. Both controllers
# inherit it: an add-on overriding a setting method must do it in a subclass
# of each controller (e.g. through its own mixin).
class AdminSSOSettingsMixin:
    """Read the add-on settings, for AdminSSO and AdminSSOHome."""

    def _auth_admin_sso_get_setting(self, name, default=None):
        """Return the setting ``name``.

        Read from the environment variable ``AUTH_ADMIN_SSO_<NAME>``, else
        from the configuration file option ``auth_admin_sso_<name>``, else
        ``default``.
        """
        return (
            os.environ.get(f"AUTH_ADMIN_SSO_{name.upper()}")
            or config.get(f"auth_admin_sso_{name.lower()}")
            or default
        )

    def _auth_admin_sso_get_settings(self):
        """Return the settings (dict), or None while a required one is missing.

        The issuer and client id are required only by the ``oidc`` provider.
        """
        get = self._auth_admin_sso_get_setting
        settings = {
            "provider": get("provider", "oidc"),
            "required_role": get("required_role"),
            "default_login": get("default_login", "admin"),
            "issuer": (get("issuer") or "").rstrip("/"),
            "client_id": get("client_id"),
            "roles_claim": get("roles_claim", "roles"),
        }
        if not settings["required_role"]:
            return None
        if settings["provider"] == "oidc":
            if not settings["issuer"] or not settings["client_id"]:
                return None
        settings["redirect_login"] = self._auth_admin_sso_get_flag("redirect_login")
        settings["redirect_keyword"] = get("redirect_keyword", "sso")
        settings["case_insensitive_login"] = self._auth_admin_sso_get_flag(
            "case_insensitive_login"
        )
        return settings

    def _auth_admin_sso_get_flag(self, name):
        """Return whether the setting ``name`` is ``1``, ``true`` or ``yes``.

        Case and surrounding spaces are ignored; missing means False.
        """
        value = (self._auth_admin_sso_get_setting(name) or "").strip().lower()
        return value in ("1", "true", "yes")

    def _auth_admin_sso_require_settings(self):
        settings = self._auth_admin_sso_get_settings()
        if not settings:
            raise NotFound()
        return settings


# Every step is an ``_auth_admin_sso_*`` method so that another add-on can
# add a provider by inheriting this controller: it overrides the provider
# methods for its own ``settings["provider"]`` value, calling ``super()``
# otherwise.
class AdminSSO(AdminSSOSettingsMixin, http.Controller):
    """Routes of the SSO login flow, with an OpenID Connect provider.

    The ``_auth_admin_sso_*`` methods raise SSOError to refuse a login
    (HTTP 403); any other exception is a technical issue (HTTP 500).
    """

    @http.route("/auth_admin_sso/login", type="http", auth="none", methods=["GET"])
    def sso_start(self):
        try:
            return self._auth_admin_sso_request_authorization()
        except HTTPException:
            raise
        except Exception as e:
            return self._auth_admin_sso_failure_response(e)

    # readonly=False: the login writes a res.users.log row. A read-only GET
    # would fail, then be retried after the PKCE data was popped from session.
    @http.route(
        "/auth_admin_sso/callback",
        type="http",
        auth="none",
        methods=["GET"],
        readonly=False,
    )
    def sso_callback(self, **kw):
        try:
            return self._auth_admin_sso_callback(**kw)
        except HTTPException:
            raise
        except Exception as e:
            return self._auth_admin_sso_failure_response(e, undo_login=True)

    # Flow methods.

    def _auth_admin_sso_request_authorization(self):
        """Return a redirect to the provider login page.

        Store the state, nonce and PKCE verifier of the attempt in the session.
        Raise NotFound while not configured, SSOError to refuse the login.
        """
        settings = self._auth_admin_sso_require_settings()
        if not request.db:
            return request.redirect("/web/database/selector")
        verifier, challenge = self._auth_admin_sso_new_pkce()
        state = secrets.token_urlsafe(32)
        nonce = secrets.token_urlsafe(32)
        url = self._auth_admin_sso_authorization_url(
            settings, self._auth_admin_sso_callback_uri(), state, nonce, challenge
        )
        self._auth_admin_sso_save_attempt(state, nonce, verifier)
        return request.redirect(url, local=False)

    def _auth_admin_sso_callback(self, code=None, state=None, **kw):
        """Log in from the provider answer; return a redirect to ``/web``.

        Raise NotFound while not configured, SSOError to refuse the login.
        """
        settings = self._auth_admin_sso_require_settings()
        nonce, verifier = self._auth_admin_sso_pop_attempt(state)
        if kw.get("error"):
            raise SSOError(f"{kw['error']}: {kw.get('error_description')}")
        if not code:
            raise SSOError("missing code")
        claims = self._auth_admin_sso_fetch_claims(
            settings, code, verifier, self._auth_admin_sso_callback_uri()
        )
        self._auth_admin_sso_check_nonce(settings, claims, nonce)
        identity = self._auth_admin_sso_get_identity(settings, claims)
        roles = self._auth_admin_sso_get_roles(settings, claims)
        try:
            login = self._auth_admin_sso_select_login(settings, roles)
        except SSOError as e:
            raise SSOError(f"{identity}: {e}") from e
        self._auth_admin_sso_login_as(login)
        _logger.info("Admin SSO: %s logged in as %s", identity, login)
        return request.redirect("/web")

    def _auth_admin_sso_failure_response(self, error, undo_login=False):
        """Return the response for ``error`` raised by the login flow.

        403 for an SSOError, else 500. With ``undo_login``, a 500 also rolls
        back the transaction and logs the session out.
        """
        if isinstance(error, SSOError):
            return self._auth_admin_sso_error_response(
                403, REFUSED_MESSAGE, f"login refused: {error}"
            )
        if undo_login:
            # Undo a half-done login (e.g. session finalized, then a failure).
            request.env.cr.rollback()
            request.session.logout(keep_db=True)
        return self._auth_admin_sso_error_response(
            500, ISSUE_MESSAGE, repr(error), True
        )

    def _auth_admin_sso_save_attempt(self, state, nonce, verifier):
        """Store the login attempt in the session."""
        request.session[SESSION_KEY] = {
            "state": state,
            "nonce": nonce,
            "verifier": verifier,
        }

    def _auth_admin_sso_pop_attempt(self, state):
        """Remove the login attempt from the session; return its nonce, verifier.

        Raise SSOError if there is none, or if its state is not ``state``.
        """
        attempt = request.session.pop(SESSION_KEY, None)
        if not attempt:
            raise SSOError("no login attempt in the session")
        if state != attempt["state"]:
            raise SSOError("state mismatch")
        return attempt["nonce"], attempt["verifier"]

    def _auth_admin_sso_error_response(self, status, message, cause, exc_info=False):
        """Log ``cause`` under a new reference; return a ``status`` response.

        The response body is ``message`` formatted with that reference only.
        """
        # The browser never gets the cause, so nothing about the configuration
        # or the provider token is disclosed: the user gives the reference to
        # an administrator, who finds the cause in the server logs.
        ref = str(uuid.uuid4())
        _logger.warning("Admin SSO [%s]: %s", ref, cause, exc_info=exc_info)
        return request.make_response(
            message.format(ref=ref),
            headers=[("Content-Type", "text/plain")],
            status=status,
        )

    def _auth_admin_sso_new_pkce(self):
        """Return a PKCE verifier and its S256 challenge."""
        verifier = secrets.token_urlsafe(64)
        challenge = (
            base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest())
            .rstrip(b"=")
            .decode()
        )
        return verifier, challenge

    def _auth_admin_sso_callback_uri(self):
        return request.httprequest.url_root.rstrip("/") + "/auth_admin_sso/callback"

    def _auth_admin_sso_select_login(self, settings, roles):
        """Return the Odoo login granted by ``roles``; raise SSOError if none.

        With P the required role:
        - a ``P.username.<username>`` role grants ``<username>``; with several
          such usernames, log a warning and grant the default login if it is
          one of them, else raise SSOError;
        - else the ``P`` role grants the default login;
        - other ``P.<keyword>.<value>`` roles are ignored.
        """
        required = settings["required_role"]
        prefix = f"{required}.username."
        usernames = {
            role.removeprefix(prefix) for role in roles if role.startswith(prefix)
        }
        usernames.discard("")
        if len(usernames) == 1:
            return usernames.pop()
        if usernames:
            _logger.warning("Admin SSO: several username roles: %s", sorted(usernames))
            if settings["default_login"] not in usernames:
                raise SSOError(f"ambiguous username roles: {sorted(usernames)}")
            return settings["default_login"]
        if required not in roles:
            raise SSOError(f"no role {required!r} nor {prefix}<username>")
        return settings["default_login"]

    def _auth_admin_sso_login_as(self, login):
        """Open an Odoo session as ``login`` without password.

        Raise SSOError if no active user has that login.
        """
        # The only Odoo-version-specific code of this module (Odoo 18).
        user = (
            request.env["res.users"]
            .sudo()
            .search([("login", "=", login), ("active", "=", True)], limit=1)
        )
        if not user:
            raise SSOError(f"no active user with login {login!r}")
        # The Odoo two-factor authentication is skipped on purpose: the
        # provider handles it.
        request.session.pre_login = user.login
        request.session.pre_uid = user.id
        request.session.finalize(request.env)
        user.with_user(user)._update_last_login()

    # Provider methods (OpenID Connect).

    def _auth_admin_sso_check_provider(self, settings):
        """Raise RuntimeError unless the provider is ``oidc`` and usable."""
        if settings["provider"] != "oidc":
            raise RuntimeError(f"unknown provider {settings['provider']!r}")
        if jwt is None:
            raise RuntimeError("python-jose not installed")

    def _auth_admin_sso_authorization_url(
        self, settings, redirect_uri, state, nonce, challenge
    ):
        """Return the provider URL to send the browser to.

        The provider redirects back to ``redirect_uri`` with the ``code`` and
        ``state`` query parameters. ``challenge`` is the S256 PKCE challenge.
        """
        self._auth_admin_sso_check_provider(settings)
        params = {
            "client_id": settings["client_id"],
            "response_type": "code",
            "response_mode": "query",
            "redirect_uri": redirect_uri,
            "scope": "openid profile email",
            "state": state,
            "nonce": nonce,
            "code_challenge": challenge,
            "code_challenge_method": "S256",
        }
        endpoint = self._auth_admin_sso_get_discovery(settings)[
            "authorization_endpoint"
        ]
        return endpoint + "?" + urlencode(params)

    def _auth_admin_sso_fetch_claims(self, settings, code, code_verifier, redirect_uri):
        """Return the claims of the user for ``code``.

        Raise SSOError unless they are verified to come from the provider.
        """
        self._auth_admin_sso_check_provider(settings)
        response = requests.post(
            self._auth_admin_sso_get_discovery(settings)["token_endpoint"],
            data={
                "client_id": settings["client_id"],
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": redirect_uri,
                "code_verifier": code_verifier,
            },
            timeout=TIMEOUT,
        )
        if not response.ok:
            raise SSOError(f"token request failed: {response.text}")
        tokens = response.json()
        return self._auth_admin_sso_verify_id_token(
            settings, tokens["id_token"], tokens.get("access_token")
        )

    def _auth_admin_sso_check_nonce(self, settings, claims, nonce):
        """Raise SSOError unless ``claims`` were issued for ``nonce``."""
        if claims.get("nonce") != nonce:
            raise SSOError("nonce mismatch")

    def _auth_admin_sso_get_roles(self, settings, claims):
        """Return the roles of the user (list of strings)."""
        roles = claims.get(settings["roles_claim"]) or []
        return [roles] if isinstance(roles, str) else list(roles)

    def _auth_admin_sso_get_identity(self, settings, claims):
        """Return who logs in, for the logs only (e.g. an email)."""
        return claims.get("email") or claims.get("preferred_username")

    def _auth_admin_sso_get_discovery(self, settings):
        """Return the OpenID Connect discovery document of the issuer."""
        issuer = settings["issuer"]
        if issuer not in _discovery_cache:
            url = issuer + "/.well-known/openid-configuration"
            response = requests.get(url, timeout=TIMEOUT)
            response.raise_for_status()
            _discovery_cache[issuer] = response.json()
        return _discovery_cache[issuer]

    def _auth_admin_sso_get_signing_key(self, settings, kid):
        jwks_uri = self._auth_admin_sso_get_discovery(settings)["jwks_uri"]
        if (jwks_uri, kid) not in _jwks_cache:
            response = requests.get(jwks_uri, timeout=TIMEOUT)
            response.raise_for_status()
            _jwks_cache.update(
                {(jwks_uri, key.get("kid")): key for key in response.json()["keys"]}
            )
        if (jwks_uri, kid) not in _jwks_cache:
            raise SSOError(f"unknown signing key {kid!r}")
        return _jwks_cache[(jwks_uri, kid)]

    def _auth_admin_sso_verify_id_token(self, settings, id_token, access_token):
        try:
            kid = jwt.get_unverified_header(id_token).get("kid")
            return jwt.decode(
                id_token,
                self._auth_admin_sso_get_signing_key(settings, kid),
                algorithms=["RS256"],
                audience=settings["client_id"],
                issuer=self._auth_admin_sso_get_discovery(settings)["issuer"],
                access_token=access_token,
            )
        except JOSEError as e:
            raise SSOError(f"invalid id_token: {e}") from e


class AdminSSOHome(AdminSSOSettingsMixin, Home):
    @http.route()
    def web_login(self, redirect=None, **kw):
        if self._auth_admin_sso_redirect_web_login():
            return request.redirect("/auth_admin_sso/login")
        return super().web_login(redirect=redirect, **kw)

    def _auth_admin_sso_redirect_web_login(self):
        """Return whether the /web/login request must go to the SSO flow.

        True for a POST of the default login with the redirect keyword as
        password, while AUTH_ADMIN_SSO_REDIRECT_LOGIN is enabled.
        """
        if request.httprequest.method != "POST":
            return False
        settings = self._auth_admin_sso_get_settings()
        if not settings or settings["redirect_login"] is not True:
            return False
        login = (request.params.get("login") or "").strip()
        default_login = settings["default_login"].strip()
        # Case-sensitive by default, as Odoo compares logins.
        if settings["case_insensitive_login"] is True:
            login = login.lower()
            default_login = default_login.lower()
        if login != default_login:
            return False
        # Plain comparison on purpose: the keyword is NOT a secret,
        # it only redirects to the SSO flow
        # => It still requires the provider login AND role.
        return request.params.get("password") == settings["redirect_keyword"]
