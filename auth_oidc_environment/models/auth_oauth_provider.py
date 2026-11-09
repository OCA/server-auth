# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models


class AuthOauthProvider(models.Model):
    _name = "auth.oauth.provider"
    _inherit = ["auth.oauth.provider", "server.env.mixin"]

    @property
    def _server_env_fields(self):
        base_fields = super()._server_env_fields
        auth_fields = {
            "client_id": {},
            "client_secret": {},
        }
        auth_fields.update(base_fields)
        return auth_fields

    @api.model
    def _server_env_global_section_name(self):
        return "auth_oauth_provider"
