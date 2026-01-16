# Copyright 2026 Kencove (https://www.kencove.com).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging
import secrets

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class SessionLogoutController(http.Controller):

    _USER_AGENT_MAX_LENGTH = 200
    _ERROR_MESSAGE_MAX_LENGTH = 500

    def _get_request_info(self):
        """Get common request information for audit logging"""
        return {
            "request_ip": request.httprequest.environ.get("REMOTE_ADDR", "Unknown"),
            "user_agent": request.httprequest.environ.get("HTTP_USER_AGENT", "")[
                : self._USER_AGENT_MAX_LENGTH
            ],
        }

    def _create_audit_log(self, status, target_user=None, error_message=None):
        """Create audit log entry"""
        vals = {
            **self._get_request_info(),
            "status": status,
        }
        if target_user:
            vals["target_user_id"] = target_user.id
        if error_message:
            vals["error_message"] = str(error_message)[: self._ERROR_MESSAGE_MAX_LENGTH]
        return request.env["auth.session.logout.audit"].sudo().create(vals)

    def _get_token_from_header(self):
        """Extract token from HTTP header.

        Supports both 'X-Force-Logout-Token' header and 'Authorization: Bearer' header.
        """
        # Check X-Force-Logout-Token header first
        token = request.httprequest.headers.get("X-Force-Logout-Token")
        if token:
            return token

        # Fall back to Authorization header with Bearer scheme
        auth_header = request.httprequest.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            return auth_header[7:]  # Remove "Bearer " prefix

        return None

    def _validate_token(self, token):
        """Validate the provided token against system parameter"""
        if not token:
            return False

        system_token = (
            request.env["ir.config_parameter"]
            .sudo()
            .get_param("auth_session_logout_api.token")
        )
        if not system_token:
            _logger.error("Logout token not configured")
            return False

        return secrets.compare_digest(token, system_token)

    def _find_user(self, user_identifier):
        """Find user by login or email (case insensitive)"""
        if not user_identifier:
            return None

        ResUsers = request.env["res.users"].sudo()

        # Try by login first (case insensitive)
        user = ResUsers.search([("login", "=ilike", user_identifier)], limit=1)

        if not user:
            # Try by email (case insensitive)
            user = ResUsers.search([("email", "=ilike", user_identifier)], limit=1)

        return user

    def _force_user_logout(self, user):
        """Force logout of all sessions for the user"""
        try:
            # Use dedicated method to handle logout and counter increment
            user.with_context(
                auth_session_logout_api_call=True
            ).sudo().action_force_logout()

            self._create_audit_log("success", target_user=user)
            _logger.info(
                "Force logout triggered for user %s from IP %s",
                user.login,
                request.httprequest.environ.get("REMOTE_ADDR"),
            )
            return True

        except Exception as e:
            _logger.exception("Failed to force logout for user %s", user.login)
            self._create_audit_log("error", target_user=user, error_message=str(e))
            return False

    @http.route(
        "/web/session/force_logout",
        type="http",
        auth="none",
        methods=["POST"],
        csrf=False,
    )
    def force_logout(self, user=None, **kwargs):
        """Force logout of user sessions

        Authentication is done via HTTP headers:
        - X-Force-Logout-Token: TOKEN
        - Or: Authorization: Bearer TOKEN

        Args:
            user (str): User login or email to logout (query param or form data)

        Returns:
            JSON response with success/error status
        """
        try:
            # Get token from header and validate
            # Avoid using the token from request parameters to prevent it
            # from being exposed in the URL and logs.
            token = self._get_token_from_header()
            if not self._validate_token(token):
                self._create_audit_log(
                    "unauthorized", error_message="Invalid or missing token"
                )
                return request.make_json_response(
                    {
                        "error": "Unauthorized",
                        "message": "Invalid or missing authentication token",
                    },
                    status=401,
                )

            # Find user
            target_user = self._find_user(user)
            if not target_user:
                self._create_audit_log(
                    "user_not_found",
                    error_message=f"User not found: {user}",
                )
                return request.make_json_response(
                    {
                        "error": "User not found",
                        "message": f'User with login or email "{user}" not found',
                    },
                    status=404,
                )

            # Force logout
            if self._force_user_logout(target_user):
                return request.make_json_response(
                    {
                        "success": True,
                        "message": f"User '{target_user.login}' has been logged out"
                        " successfully",
                    }
                )
            else:
                return request.make_json_response(
                    {
                        "error": "Internal error",
                        "message": "Failed to logout user. Please check logs for details.",
                    },
                    status=500,
                )

        except Exception as e:
            _logger.exception("Unexpected error in force_logout")
            self._create_audit_log("error", error_message=str(e))
            return request.make_json_response(
                {
                    "error": "Internal server error",
                    "message": "An unexpected error occurred. Please contact administrator.",
                },
                status=500,
            )
