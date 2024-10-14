# Copyright 2018 ACSONE SA/NV
# Copyright 2021 Camptocamp SA
# @author: Simone Orsi <simone.orsi@camptocamp.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).


from odoo import models


class AuthApiKey(models.Model):
    _name = "auth.api.key"
    _inherit = ["auth.api.key", "server.env.techname.mixin", "server.env.mixin"]

    def _server_env_section_name(self):
        """Name of the section in the configuration files
        We override the default implementation to keep the compatibility
        with the previous implementation of auth_api_key. The section name
        into the configuration file must be formatted as
            'api_key_{name}'
        """
        self.ensure_one()
        return f"api_key_{getattr(self, self._server_env_section_name_field)}"

    @property
    def _server_env_fields(self):
        base_fields = super()._server_env_fields
        api_key_fields = {"key": {}}
        api_key_fields.update(base_fields)
        return api_key_fields
