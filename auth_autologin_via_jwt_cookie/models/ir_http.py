# Copyright 2025 Kencove (https://www.kencove.com/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging
from functools import lru_cache

import jwt
import requests
from jwt import PyJWKClient
from jwt.exceptions import InvalidTokenError, PyJWTError

from odoo import models
from odoo.http import request
from odoo.service import security

_logger = logging.getLogger(__name__)


@lru_cache(maxsize=16)
def _get_jwk_client(jwks_url: str) -> PyJWKClient:
    """
    Cache a PyJWKClient per JWKS URL (per worker).
    PyJWKClient itself caches fetched JWKS keys.
    """
    return PyJWKClient(jwks_url)


class IrHttp(models.AbstractModel):
    _inherit = "ir.http"

    @classmethod
    def _authenticate(cls, endpoint):
        # If already authenticated, keep default flow
        if getattr(request, "session", None) and request.session.uid:
            return super()._authenticate(endpoint)

        result = cls._try_autologin_from_jwt_cookie()

        if not result:
            return super()._authenticate(endpoint)

    @classmethod
    def _try_autologin_from_jwt_cookie(cls):
        settings = cls._get_autologin_settings()
        if not settings:
            _logger.debug("JWT autologin disabled: missing config parameters")
            return False

        token = cls._get_cookie_token(settings["cookie_name"])
        if not token:
            _logger.debug(
                "JWT autologin skipped: cookie '%s' not found",
                settings["cookie_name"],
            )
            return False

        claims = cls._verify_jwt_with_pyjwt(token, settings["jwks_url"])
        if not claims:
            _logger.debug("JWT autologin failed: token verification returned no claims")
            return False

        # Optional hardening: accept only access tokens when claim exists
        token_use = claims.get("token_use")
        if token_use and token_use != "access":
            _logger.debug("Skipping autologin: token_use=%s", token_use)
            return False

        email = cls._get_email_from_userinfo(settings["userinfo_url"], token)
        if not email:
            _logger.debug("JWT autologin failed: email not found in userinfo response")
            return False

        user = cls._find_user_by_email(email)
        if not user:
            _logger.debug(
                "JWT autologin failed: no active user found for email=%s",
                email,
            )
            return False

        cls._force_login(user)

        return True

    @classmethod
    def _get_autologin_settings(cls):
        icp = request.env["ir.config_parameter"].sudo()
        cookie_name = (
            icp.get_param("auth_autologin_via_jwt_cookie.jwt_cookie_name") or ""
        ).strip()
        jwks_url = (
            icp.get_param("auth_autologin_via_jwt_cookie.jwks_url") or ""
        ).strip()
        userinfo_url = (
            icp.get_param("auth_autologin_via_jwt_cookie.userinfo_url") or ""
        ).strip()

        if not (cookie_name and jwks_url and userinfo_url):
            _logger.debug(
                "JWT autologin config incomplete: cookie_name=%s, jwks_url=%s, userinfo_url=%s",
                bool(cookie_name),
                bool(jwks_url),
                bool(userinfo_url),
            )
            return None
        return {
            "cookie_name": cookie_name,
            "jwks_url": jwks_url,
            "userinfo_url": userinfo_url,
        }

    @classmethod
    def _get_cookie_token(cls, cookie_name: str):
        return request.httprequest.cookies.get(cookie_name)

    @classmethod
    def _verify_jwt_with_pyjwt(cls, token: str, jwks_url: str):
        """
        Verify RS256 token using JWKS URL via PyJWKClient (cached).
        Returns claims dict if valid, otherwise None.
        """
        try:
            header = jwt.get_unverified_header(token)
        except PyJWTError as e:
            _logger.info("Invalid JWT header: %s", e)
            return None

        if header.get("alg") != "RS256":
            _logger.info("Skipping autologin: unexpected alg=%s", header.get("alg"))
            return None

        if not header.get("kid"):
            _logger.info("Skipping autologin: missing kid")
            return None

        try:
            jwk_client = _get_jwk_client(jwks_url)
            signing_key = jwk_client.get_signing_key_from_jwt(token).key
        except (requests.RequestException, PyJWTError) as e:
            _logger.warning("Unable to fetch/resolve JWKS signing key: %s", e)
            return None

        try:
            claims = jwt.decode(
                token,
                signing_key,
                algorithms=["RS256"],
                options={
                    "verify_aud": False,
                },
            )
            return claims
        except InvalidTokenError as e:
            _logger.info("JWT verification failed: %s", e)
            return None

    @classmethod
    def _get_email_from_userinfo(cls, userinfo_url: str, token: str):
        try:
            res = requests.get(
                userinfo_url,
                headers={"Authorization": f"Bearer {token}"},
                timeout=5,
            )
            res.raise_for_status()
        except requests.RequestException as e:
            _logger.warning("Userinfo request failed: %s", e)
            return None

        try:
            data = res.json()
        except ValueError:
            _logger.info("Userinfo response is not JSON")
            return None

        email = (data.get("email") or "").strip()
        return email or None

    @classmethod
    def _find_user_by_email(cls, email: str):
        user = (
            request.env["res.users"]
            .sudo()
            .search(
                ["|", ("login", "=ilike", email), ("email", "=ilike", email)],
                limit=1,
            )
        )
        return user if user and user.active else None

    @classmethod
    def _force_login(cls, user):
        request.update_env(user=user.id)
        request.session.uid = user.id
        request.session.session_token = security.compute_session_token(
            request.session, request.env
        )

        _logger.info("Auto-authenticated user %s via JWT cookie", user.login)
