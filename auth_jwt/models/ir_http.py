# Copyright 2021 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import logging

from odoo import SUPERUSER_ID, api, models
from odoo.http import request

from ..exceptions import (
    ConfigurationError,
    Unauthorized,
    UnauthorizedCompositeJwtError,
    UnauthorizedMissingAuthorizationHeader,
    UnauthorizedMissingCookie,
    UnauthorizedSessionMismatch,
)

_logger = logging.getLogger(__name__)


class IrHttpJwt(models.AbstractModel):
    _inherit = "ir.http"

    @classmethod
    def _authenticate(cls, endpoint):
        """Protect the _authenticate method.

        This is to ensure that the _authenticate method is called
        in the correct conditions to invoke _auth_method_jwt below.
        When migrating, review this method carefully by reading the original
        _authenticate method and make sure the conditions have not changed.
        """
        auth_method = endpoint.routing["auth"]
        if (
            auth_method in ("jwt", "public_or_jwt")
            or auth_method.startswith("jwt_")
            or auth_method.startswith("public_or_jwt_")
        ):
            if request.session.uid:
                _logger.warning(
                    'A route with auth="jwt" must not be used within a user session.'
                )
                raise UnauthorizedSessionMismatch()
            # Odoo calls _authenticate more than once (in v14? why?), so
            # on the second call we have a request uid and that is not an error
            # because _authenticate will not call _auth_method_jwt a second time.
            if request.uid and not hasattr(request, "jwt_payload"):
                _logger.error(
                    "A route with auth='jwt' should not have a request.uid here."
                )
                raise UnauthorizedSessionMismatch()
        return super()._authenticate(endpoint)

    @classmethod
    def _get_jwt_payload(cls, validator):
        """Obtain and validate the JWT payload from the request authorization header or
        cookie."""
        try:
            token = cls._get_bearer_token()
            assert token
            return validator._decode(token)
        except UnauthorizedMissingAuthorizationHeader:
            if not validator.cookie_enabled:
                raise
            token = cls._get_cookie_token(validator.cookie_name)
            assert token
            return validator._decode(token, secret=validator._get_jwt_cookie_secret())

    @classmethod
    def _auth_method_jwt(cls, validator_name=None):
        assert not request.uid
        assert not request.session.uid
        # # Use request cursor to allow partner creation strategy in validator
        env = api.Environment(request.cr, SUPERUSER_ID, {})
        validator = env["auth.jwt.validator"]._get_validator_by_name(validator_name)
        assert len(validator) == 1

        payload = None
        exceptions = {}
        while validator:
            try:
                payload = cls._get_jwt_payload(validator)
                break
            except Unauthorized as e:
                exceptions[validator.name] = e
                validator = validator.next_validator_id

        if not payload:
            if len(exceptions) == 1:
                raise list(exceptions.values())[0]
            raise UnauthorizedCompositeJwtError(exceptions)

        if validator.cookie_enabled:
            if not validator.cookie_name:
                _logger.info("Cookie name not set for validator %s", validator.name)
                raise ConfigurationError()
            request.future_response.set_cookie(
                key=validator.cookie_name,
                value=validator._encode(
                    payload,
                    secret=validator._get_jwt_cookie_secret(),
                    expire=validator.cookie_max_age,
                ),
                max_age=validator.cookie_max_age,
                path=validator.cookie_path or "/",
                secure=validator.cookie_secure,
                httponly=True,
            )

        uid = validator._get_and_check_uid(payload)
        assert uid
        partner_id = validator._get_and_check_partner_id(payload)
        request.update_env(user=uid)
        request.jwt_payload = payload
        request.jwt_partner_id = partner_id

    @classmethod
    def _auth_method_public_or_jwt(cls, validator_name=None):
        if "HTTP_AUTHORIZATION" not in request.httprequest.environ:
            env = api.Environment(request.cr, SUPERUSER_ID, {})
            validator = env["auth.jwt.validator"]._get_validator_by_name(validator_name)
            assert len(validator) == 1
            if not validator.cookie_enabled or not request.httprequest.cookies.get(
                validator.cookie_name
            ):
                return cls._auth_method_public()
        return cls._auth_method_jwt(validator_name)

    @classmethod
    def _get_bearer_token(cls):
        # https://tools.ietf.org/html/rfc2617#section-3.2.2
        authorization = request.httprequest.environ.get("HTTP_AUTHORIZATION")
        return request.env["auth.jwt.validator"]._parse_bearer_authorization(
            authorization
        )

    @classmethod
    def _get_cookie_token(cls, cookie_name):
        token = request.httprequest.cookies.get(cookie_name)
        if not token:
            _logger.info("Missing cookie %s.", cookie_name)
            raise UnauthorizedMissingCookie()
        return token
