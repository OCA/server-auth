# Copyright 2021 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl)

from werkzeug.exceptions import InternalServerError, Unauthorized


class UnauthorizedMissingAuthorizationHeader(Unauthorized):
    pass


class UnauthorizedMissingCookie(Unauthorized):
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


class UnauthorizedCompositeJwtError(Unauthorized):
    """Indicate that multiple errors occurred during JWT chain validation."""

    def __init__(self, errors):
        self.errors = errors
        super().__init__(
            "Multiple errors occurred during JWT chain validation:\n"
            + "\n".join(
                f"{validator_name}: {error}"
                for validator_name, error in self.errors.items()
            )
        )


class ConfigurationError(InternalServerError):
    pass
