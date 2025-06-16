# Copyright 2025 Alberto Martínez <alberto.martinez@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from odoo import fields, models

from odoo.addons.base.models.res_users import check_identity


class APIKeyDescription(models.TransientModel):
    _inherit = "res.users.apikeys.description"

    scope = fields.Selection(
        [("rpc", "rpc")],
    )
    has_custom_scope = fields.Boolean()
    custom_scope = fields.Char()

    @check_identity
    def make_key(self):
        return super(
            APIKeyDescription,
            self.with_context(
                apikey_scope=self.scope
                if not self.has_custom_scope
                else self.custom_scope
            ),
        ).make_key()
