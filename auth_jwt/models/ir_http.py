# Copyright 2021 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import logging
import re

from odoo import SUPERUSER_ID, api, models
from odoo.http import request

from ..exceptions import (
    CompositeJwtError,
    UnauthorizedMalformedAuthorizationHeader,
    UnauthorizedMissingAuthorizationHeader,
    UnauthorizedSessionMismatch,
)

_logger = logging.getLogger(__name__)


AUTHORIZATION_RE = re.compile(r"^Bearer ([^ ]+)$")


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
    def _auth_method_jwt(cls, validator_name=None):
        assert not request.uid
        assert not request.session.uid
        token = cls._get_bearer_token()
        assert token
        # # Use request cursor to allow partner creation strategy in validator
        env = api.Environment(request.cr, SUPERUSER_ID, {})
        validator = env["auth.jwt.validator"]._get_validator_by_name(validator_name)
        assert len(validator) == 1

        payload = None
        exceptions = {}
        while validator:
            try:
                payload = validator._decode(token)
                break
            except Exception as e:
                exceptions[validator.name] = e
                validator = validator.next_validator_id

        if not payload:
            if len(exceptions) == 1:
                raise list(exceptions.values())[0]
            raise CompositeJwtError(exceptions)

        uid = validator._get_and_check_uid(payload)
        assert uid
        partner_id = validator._get_and_check_partner_id(payload)
        request.uid = uid  # this resets request.env
        request.jwt_payload = payload
        request.jwt_partner_id = partner_id

    @classmethod
    def _auth_method_public_or_jwt(cls, validator_name=None):
        if "HTTP_AUTHORIZATION" not in request.httprequest.environ:
            return cls._auth_method_public()
        return cls._auth_method_jwt(validator_name)

    @classmethod
    def _get_bearer_token(cls):
        # https://tools.ietf.org/html/rfc2617#section-3.2.2
        authorization = request.httprequest.environ.get("HTTP_AUTHORIZATION")
        if not authorization:
            _logger.info("Missing Authorization header.")
            raise UnauthorizedMissingAuthorizationHeader()
        # https://tools.ietf.org/html/rfc6750#section-2.1
        mo = AUTHORIZATION_RE.match(authorization)
        if not mo:
            _logger.info("Malformed Authorization header.")
            raise UnauthorizedMalformedAuthorizationHeader()
        return mo.group(1)
