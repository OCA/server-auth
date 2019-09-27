# Copyright 2018 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models, tools, _

from odoo.tools import consteq

from odoo.exceptions import ValidationError, AccessError


class AuthApiKey(models.Model):
    _name = "auth.api.key"
    _inherit = "server.env.mixin"
    _description = "API Key"

    name = fields.Char(required=True)
    key = fields.Char(
        required=True,
        help="""The API key. Enter a dummy value in this field if it is
        obtained from the server environment configuration.""",
    )
    user_id = fields.Many2one(
        comodel_name="res.users",
        string="User",
        required=True,
        help="""The user used to process the requests authenticated by
        the api key""",
    )

    _sql_constraints = [
        ("name_uniq", "unique(name)", "Api Key name must be unique.")
    ]

    @api.multi
    def _server_env_section_name(self):
        """Name of the section in the configuration files

        We override the default implementation to keep the compatibility
        with the previous implementation of auth_api_key. The section name
        into the configuration file must be formatted as

            'api_key_{name}'

        """
        self.ensure_one()
        return "api_key_{}".format(self.name)

    @property
    def _server_env_fields(self):
        base_fields = super()._server_env_fields
        api_key_fields = {"key": {}}
        api_key_fields.update(base_fields)
        return api_key_fields

    @api.model
    def _retrieve_api_key(self, key):
        return self.browse(self._retrieve_api_key_id(key))

    @api.model
    @tools.ormcache("key")
    def _retrieve_api_key_id(self, key):
        if not self.env.user.has_group("base.group_system"):
            raise AccessError(_("User is not allowed"))
        for api_key in self.search([]):
            if consteq(key, api_key.key):
                return api_key.id
        raise ValidationError(_("The key %s is not allowed") % key)

    @api.model
    @tools.ormcache("key")
    def _retrieve_uid_from_api_key(self, key):
        return self._retrieve_api_key(key).user_id.id

    def _clear_key_cache(self):
        self._retrieve_api_key_id.clear_cache(self.env[self._name])
        self._retrieve_uid_from_api_key.clear_cache(self.env[self._name])

    @api.model
    def create(self, vals):
        record = super(AuthApiKey, self).create(vals)
        if "key" in vals or "user_id" in vals:
            self._clear_key_cache()
        return record

    def write(self, vals):
        super(AuthApiKey, self).write(vals)
        if "key" in vals or "user_id" in vals:
            self._clear_key_cache()
        return True
