# Copyright 2018 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import _, api, fields, models, tools
from odoo.exceptions import AccessError, ValidationError
from odoo.tools import consteq


class AuthApiKey(models.Model):
    _name = "auth.api.key"
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
    # Not using related to stay backward compatible with having active keys
    # for archived users (no need being invoiced by Odoo for api request users)
    active = fields.Boolean(
        compute="_compute_active", readonly=False, store=True, default=True
    )

    _sql_constraints = [("name_uniq", "unique(name)", "Api Key name must be unique.")]

    @api.model
    def _retrieve_api_key(self, key):
        return self.browse(self._retrieve_api_key_id(key))

    @api.model
    @tools.ormcache("key")
    def _retrieve_api_key_id(self, key):
        if not self.env.user.has_group("base.group_system"):
            raise AccessError(_("User is not allowed"))
        for api_key in self.search([]):
            if api_key.key and consteq(key, api_key.key):
                return api_key.id
        raise ValidationError(_(f"The key {key} is not allowed"))

    @api.model
    @tools.ormcache("key")
    def _retrieve_uid_from_api_key(self, key):
        return self._retrieve_api_key(key).user_id.id

    def _clear_key_cache(self):
        self.env.registry.clear_cache()

    @api.depends(
        "user_id.active", "user_id.company_id.archived_user_disable_auth_api_key"
    )
    def _compute_active(self):
        option_disable_key = self.user_id.company_id.archived_user_disable_auth_api_key
        for record in self:
            if option_disable_key:
                record.active = record.user_id.active
            # To stay coherent if the option is disabled the active field is not
            # changed. Because the field is stored, it should not be an issue.

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        if any(["key" in vals or "user_id" in vals for vals in vals_list]):
            self._clear_key_cache()
        return records

    def write(self, vals):
        super().write(vals)
        if "key" in vals or "user_id" in vals:
            self._clear_key_cache()
        return True
