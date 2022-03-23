# Copyright 2018 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
import uuid

from odoo import api, fields, models, tools, _
from odoo.tools import consteq
from odoo.exceptions import ValidationError, AccessError


class AuthApiKey(models.Model):
    _name = "auth.api.key"
    _description = "API Key"

    def _default_key(self):
        return uuid.uuid4()

    name = fields.Char(required=True)
    key = fields.Char(
        required=True,
        default=lambda self: self._default_key(),
        help="""The API key. Keep the default value in this field if it is
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
