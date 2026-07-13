# Copyright 2026 Trobz
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from contextlib import ExitStack
from datetime import timedelta, timezone

import odoo
from odoo import fields, http
from odoo.exceptions import AccessDenied
from odoo.http import Controller, request, route

_logger = logging.getLogger(__name__)

# Default validity window for a generated API key, in days. Can be overridden
# through the ``auth_api_key_native_generate.duration`` system parameter.
DEFAULT_DURATION_DAYS = 90

# The endpoint is unauthenticated (auth="none"); cap the request body to a small
# size so it cannot be abused to feed large payloads into memory. Odoo's default
# limit is 128MiB, far more than a credentials payload ever needs.
MAX_CONTENT_LENGTH = 8 * 1024  # 8 KiB


class AuthApiKeyNativeGenerate(Controller):
    def _get_api_key_duration(self, env):
        """Return the configured validity duration (in days) for new keys."""
        param = (
            env["ir.config_parameter"]
            .sudo()
            .get_param("auth_api_key_native_generate.duration")
        )
        try:
            duration = int(param)
        except (TypeError, ValueError):
            return DEFAULT_DURATION_DAYS
        return duration if duration > 0 else DEFAULT_DURATION_DAYS

    @route(
        "/api/auth/generate_api_key",
        type="http",
        auth="none",
        methods=["POST"],
        csrf=False,
        save_session=False,
        readonly=False,
        max_content_length=MAX_CONTENT_LENGTH,
    )
    def generate_api_key(self):
        """Exchange user credentials for a native Odoo API key.

        Request body (JSON)::

            {"db": "...", "login": "...", "password": "..."}

        Response body (JSON)::

            {"api_key": "...", "expiration_date": "..."}

        The credentials are verified through the native
        ``res.users.authenticate`` path, which relies on ``_assert_can_auth``
        for the built-in login cooldown protection. On success a new API key is
        issued with ``res.users.apikeys._generate`` using the ``rpc`` scope and
        a fixed validity window (default 90 days, configurable in the settings).
        """
        try:
            data = request.get_json_data()
        except ValueError:
            return request.make_json_response(
                {"error": "Invalid JSON body."}, status=400
            )
        # get_json_data() does no shape validation: reject anything that is not
        # a JSON object so the .get() calls below cannot raise a 500.
        if not isinstance(data, dict):
            return request.make_json_response(
                {"error": "Request body must be a JSON object."}, status=400
            )

        db = data.get("db")
        login = data.get("login")
        password = data.get("password")
        if not (db and login and password):
            return request.make_json_response(
                {"error": "'db', 'login' and 'password' are required."}, status=400
            )

        if not http.db_filter([db]):
            return request.make_json_response(
                {"error": "Database not found."}, status=404
            )

        with ExitStack() as stack:
            if not request.db or request.db != db:
                # Open a dedicated cursor/env when the request is not already
                # bound to the requested database. The cursor is committed on a
                # clean exit of the ExitStack, persisting the new key.
                try:
                    registry = odoo.modules.registry.Registry(db)
                except Exception:
                    _logger.warning("Database %r not found or not reachable.", db)
                    return request.make_json_response(
                        {"error": "Database not found."}, status=404
                    )
                cr = stack.enter_context(registry.cursor())
                env = odoo.api.Environment(cr, None, {})
            else:
                env = request.env(user=None, su=False)

            credential = {"login": login, "password": password, "type": "password"}
            # "interactive": True selects the password-login path in
            # _check_credentials (verify the real password, not treat it as an
            # API key) and silences the "assuming interactive login" warning.
            try:
                auth_info = env["res.users"].authenticate(
                    credential, {"interactive": True}
                )
            except AccessDenied:
                return request.make_json_response(
                    {"error": "Invalid credentials."}, status=401
                )

            uid = auth_info["uid"]
            # Enforce the same MFA gate as the native login flow
            # (see Session.authenticate / odoo.http). This endpoint only accepts
            # a password, so a user with two-factor authentication enabled must
            # not be able to obtain an API key by password alone.
            user = env["res.users"].browse(uid)
            if auth_info.get("mfa") != "skip" and user._mfa_url():
                return request.make_json_response(
                    {
                        "error": "Two-factor authentication is enabled for this "
                        "user; API key generation from a password is not allowed."
                    },
                    status=403,
                )
            duration = self._get_api_key_duration(env)
            # fields.Datetime.now() returns naive UTC, matching how Odoo stores
            # and compares apikeys.expiration_date (now() at time zone 'utc').
            # The response below serializes it timezone-aware to be explicit
            # towards external clients.
            expiration_date = fields.Datetime.now() + timedelta(days=duration)

            # Generate the key as the authenticated user, in superuser mode so
            # the fixed validity window is not capped by the user's group
            # ``api_key_duration`` limit. Keeping ``uid`` ensures the key is
            # owned by the authenticated user, not the superuser.
            key_env = env(user=uid, su=True)
            api_key = key_env["res.users.apikeys"]._generate(
                scope="rpc",
                name="Generated via /api/auth/generate_api_key",
                expiration_date=expiration_date,
            )

            return request.make_json_response(
                {
                    "api_key": api_key,
                    "expiration_date": expiration_date.replace(
                        tzinfo=timezone.utc
                    ).isoformat(),
                }
            )
