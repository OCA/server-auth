# Copyright 2026 Lorenzo Battistini
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from werkzeug.exceptions import Forbidden


class OAuthError(Exception):
    """An OAuth error, answered to the client as defined by RFC 6749.

    ``error`` is the RFC error code; ``description`` is meant for developers
    and is therefore not translated.
    """

    def __init__(self, error, description=None, status=400):
        super().__init__(description or error)
        self.error = error
        self.description = description
        self.status = status

    def to_dict(self):
        res = {"error": self.error}
        if self.description:
            res["error_description"] = self.description
        return res


class InsufficientScope(Forbidden):
    """The access token is valid but lacks scopes the resource requires."""

    def __init__(self, scope, description=None):
        super().__init__(description)
        self.scope = scope
