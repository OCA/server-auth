# Copyright 2018 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models, tools, _

from odoo.tools import consteq

from odoo.exceptions import ValidationError, AccessError


class AuthApiKey(models.Model):
    _name = "auth.api.key"
    _inherit = "server.env.mixin"
    _description = "API Key Retriever"

    name = fields.Char(required=True)
    key = fields.Char(required=True)
    user_id = fields.Many2one(
        comodel_name="res.users",
        string="User",
        required=True,
        help="""The user used to process the requests authenticated by
        the api key"""
    )

    @property
    def _server_env_fields(self):
        base_fields = super()._server_env_fields
        api_key_fields = {
            "key": {},
        }
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
        if 'key' in vals:
            self._clear_key_cache()
        return record

    def write(self, vals):
        super(AuthApiKey, self).write(vals)
        if 'key' in vals:
            self._clear_key_cache()
        return True
