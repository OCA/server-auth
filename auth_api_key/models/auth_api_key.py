# Copyright 2018 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, models, tools, _

from odoo.tools import consteq

from odoo.exceptions import ValidationError, AccessError


class AuthApiKey(models.Model):
    _name = "auth.api.key"
    _inherit = "server.env.mixin"
    _description = "API Key Retriever"

    name = fields.Char(required=True)
    key = fields.Char(required=True)
    user = fields.Char(required=True)

    _sql_constraints = [
        ('key_uniq', 'unique(key)', 'API Key Retriever must be unique !'),
    ]

    @property
    def _server_env_fields(self):
        base_fields = super()._server_env_fields
        api_key_fields = {
            "key": {},
            "user": {},
        }
        api_key_fields.update(base_fields)
        return api_key_fields

    @api.model
    @tools.ormcache("api_key")
    def _retrieve_api_key(self, api_key):
        if not self.env.user.has_group("base.group_system"):
            raise AccessError(_("User is not allowed"))
        ap_keys = self.search([])
        # api key are a computed field in the context of server env
        # so we can't use a domain in search method
        key = False
        for ap_key in ap_keys:
            if consteq(api_key, ap_key.key):
                key = ap_key

        if not key:
            raise ValidationError(
                _("The key %s is not defined") % api_key)

        return key

    @api.model
    @tools.ormcache("api_key")
    def _retrieve_uid_from_api_key(self, api_key):
        ap_key = self._retrieve_api_key(api_key)
        uid = self.env["res.users"].search(
                    [("login", "=", ap_key.user)]).id

        if not uid:
            raise ValidationError(
                _("No user found with login %s") % ap_key.user)

        return uid
    return False

