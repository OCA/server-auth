# Copyright 2021 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl)

from werkzeug.exceptions import InternalServerError, Unauthorized


class UnauthorizedMissingAuthorizationHeader(Unauthorized):
    pass


class UnauthorizedMalformedAuthorizationHeader(Unauthorized):
    pass


class UnauthorizedSessionMismatch(Unauthorized):
    pass


class AmbiguousJwtValidator(InternalServerError):
    pass


class JwtValidatorNotFound(InternalServerError):
    pass


class UnauthorizedInvalidToken(Unauthorized):
    pass


class UnauthorizedPartnerNotFound(Unauthorized):
    pass
