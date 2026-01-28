# Copyright 2026 Kencove (https://www.kencove.com).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import json
import logging
import time

from odoo import api, fields, http
from odoo.exceptions import AccessError, MissingError, UserError, ValidationError
from odoo.http import request
from odoo.service.model import get_public_method

_logger = logging.getLogger(__name__)


class AuthExecuteAsController(http.Controller):
    @http.route("/execute_as", type="json", auth="none", methods=["POST"], csrf=False)
    def execute_as(self, **kwargs):
        """
        Execute an API call as a specific user with whitelist-based access control.
        """
        start_time = time.time()

        # Get request data
        params = (
            request.get_json_data() if hasattr(request, "get_json_data") else kwargs
        )
        login = params.get("login")
        model_name = params.get("model")
        method_name = params.get("method")
        args = params.get("args", [])
        method_kwargs = params.get("kwargs", {})

        # Calculate request size
        request_payload = json.dumps(params, default=str)
        request_size = len(request_payload.encode("utf-8"))

        # Initialize log data
        log_data = {
            "model_name": model_name,
            "method": method_name,
            "request_payload": request_payload,
            "request_size_bytes": request_size,
        }

        whitelist = None
        truncate = True
        try:
            # 1. Authentication & Authorization
            client, whitelist, user, error = self._validate_request(
                login, model_name, method_name, log_data
            )
            if error:
                return error

            log_data["client_id"] = client.id
            log_data["user_id"] = user.id
            truncate = whitelist.truncate_response

            # 2. Field Filtering
            if method_name in ("read", "search_read") and "fields" in method_kwargs:
                method_kwargs["fields"] = self._filter_fields(
                    whitelist, method_kwargs.get("fields", [])
                )

            # 3. Execution - Execute method as the target user
            env = request.env(user=user.id)
            model = env[model_name]

            # Validate method exists and is public (checks _ prefix and @api.private)
            try:
                get_public_method(model, method_name)
            except AttributeError:
                return self._error_response(
                    403,
                    f"Method '{method_name}' not found or not allowed on model '{model_name}'",
                    log_data,
                    truncate,
                )

            result = api.call_kw(model, method_name, args, method_kwargs)

            # 4. Finalize and return
            return self._finalize_response(result, whitelist, log_data, start_time)

        except AccessError as e:
            return self._error_response(403, str(e), log_data, truncate)
        except MissingError as e:
            return self._error_response(404, str(e), log_data, truncate)
        except (ValidationError, UserError) as e:
            return self._error_response(422, str(e), log_data, truncate)
        except Exception as e:
            _logger.exception("Error in /execute_as endpoint")
            return self._error_response(500, str(e), log_data, truncate)

    # ==================== Helper Methods ====================

    def _validation_error(self, status_code, message, log_data, truncate=False):
        """Return a validation failure tuple."""
        return (
            None,
            None,
            None,
            self._error_response(status_code, message, log_data, truncate),
        )

    def _validate_request(self, login, model_name, method_name, log_data):
        """Validate authentication, authorization, and return client/whitelist/user."""
        # Authentication - Validate API Key
        api_key = request.httprequest.headers.get("X-API-Key")
        if not api_key:
            return self._validation_error(401, "Missing API Key", log_data)

        client = self._authenticate_client(api_key)
        if not client:
            return self._validation_error(401, "Invalid API Key", log_data)

        # Check token expiry
        if client.is_token_expired():
            return self._validation_error(401, "Token has expired", log_data)

        # Check IP whitelist
        client_ip = request.httprequest.remote_addr
        if not client.is_ip_allowed(client_ip):
            return self._validation_error(
                403, f"IP address '{client_ip}' is not allowed", log_data
            )

        # Authorization - Check Whitelist
        whitelist = self._check_whitelist(
            client.whitelist_id.id, model_name, method_name
        )
        if not whitelist:
            return self._validation_error(
                403,
                f"Method '{method_name}' on model '{model_name}' is not allowed",
                log_data,
            )

        # Impersonation - Find and switch to target user
        user = self._find_user(login)
        if not user:
            return self._validation_error(
                404, f"User with login '{login}' not found", log_data
            )

        # Check user whitelist
        if not client.is_user_allowed(user):
            return self._validation_error(
                403, f"User '{login}' is not allowed for this client", log_data
            )

        return client, whitelist, user, None

    def _authenticate_client(self, api_key):
        """Find and return active client by API key."""
        return (
            request.env["auth.api.client"]
            .sudo()
            .search([("secret_token", "=", api_key), ("active", "=", True)], limit=1)
        )

    def _check_whitelist(self, whitelist_id, model_name, method_name):
        """Check if model/method is in whitelist."""
        if not whitelist_id:
            return False

        whitelist = request.env["auth.api.whitelist"].sudo().browse(whitelist_id)
        if not whitelist.exists():
            return False

        whitelist_line = whitelist.line_ids.filtered(
            lambda w: w.model_id.model == model_name and w.method == method_name
        )
        return whitelist_line[:1] if whitelist_line else False

    def _find_user(self, login):
        """Find user by login."""
        return (
            request.env["res.users"]
            .sudo()
            .search([("login", "=", login), ("active", "=", True)], limit=1)
        )

    def _filter_fields(self, whitelist, requested_fields):
        """Filter requested fields based on whitelist configuration."""
        if not whitelist.field_ids:
            return requested_fields

        allowed_fields = whitelist.field_ids.mapped("name")
        return [f for f in requested_fields if f in allowed_fields]

    def _clean_data(self, data):
        """Clean data: convert dates to ISO format, simplify Many2one (id, name) to name."""
        if isinstance(data, (list, tuple)) and not self._is_many2one_tuple(data):
            return [self._clean_data(item) for item in data]
        elif isinstance(data, dict):
            cleaned = {}
            for key, value in data.items():
                if isinstance(value, (fields.Date, fields.Datetime)):
                    cleaned[key] = value.isoformat()
                elif self._is_many2one_tuple(value):
                    # Many2one field: (id, name) -> name
                    cleaned[key] = value[1]
                else:
                    cleaned[key] = self._clean_data(value)
            return cleaned
        elif isinstance(data, (fields.Date, fields.Datetime)):
            return data.isoformat()
        return data

    def _is_many2one_tuple(self, value):
        """Check if value is a Many2one tuple (id, name)."""
        return (
            isinstance(value, tuple)
            and len(value) == 2
            and isinstance(value[0], int)
            and isinstance(value[1], str)
        )

    def _finalize_response(self, result, whitelist, log_data, start_time):
        """Clean data, log, and return response."""
        # Apply clean_response setting from whitelist
        clean = whitelist.clean_response if whitelist else True
        if clean:
            result = self._clean_data(result)

        # Get logging settings from whitelist
        log_call = whitelist.log_call if whitelist else True
        log_response = whitelist.log_response if whitelist else True
        truncate_response = whitelist.truncate_response if whitelist else True

        if log_call:
            # Calculate sizes and timing
            response_json = json.dumps(result, default=str)
            log_data["status_code"] = 200
            log_data["execution_time_ms"] = int((time.time() - start_time) * 1000)
            log_data["response_size_bytes"] = len(response_json.encode("utf-8"))

            if log_response:
                if truncate_response:
                    log_data["response_payload"] = response_json[:1000]
                else:
                    log_data["response_payload"] = response_json

            self._create_log(log_data)

        return result

    def _error_response(self, status_code, message, log_data, truncate=True):
        """Create error response and log it."""
        response_json = json.dumps({"error": message})
        log_data["status_code"] = status_code
        log_data["response_size_bytes"] = len(response_json.encode("utf-8"))
        if truncate:
            log_data["response_payload"] = response_json[:1000]
        else:
            log_data["response_payload"] = response_json
        self._create_log(log_data)

        return {"error": message, "status_code": status_code}

    def _create_log(self, log_data):
        """Create API log entry using sudo to ensure it's always recorded."""
        try:
            request.env["auth.api.log"].sudo().create(log_data)
        except Exception:
            _logger.exception("Failed to create API log")
