# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class AuthJwtValidator(models.Model):

    _name = "auth.jwt.validator"
    _inherit = ["auth.jwt.validator", "server.env.mixin"]

    @property
    def _server_env_fields(self):
        env_fields = super()._server_env_fields
        env_fields.update(
            {"secret_key": {}, "audience": {}, "issuer": {}, "public_key_jwk_uri": {}}
        )
        return env_fields
