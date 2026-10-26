# Copyright 2026 Lorenzo Battistini
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models
from odoo.osv import expression


class AuthJwtValidator(models.Model):
    _inherit = "auth.jwt.validator"

    user_id_strategy = fields.Selection(
        selection_add=[("oauth_server", "OAuth Server Authorization")],
        ondelete={"oauth_server": "cascade"},
    )
    oauth_server_resource_ids = fields.One2many(
        "oauth.server.resource", "jwt_validator_id", readonly=True
    )

    @api.model
    def _get_validator_by_name_domain(self, validator_name):
        """Keep the validators of the authorization server out of routes that
        name no validator (``auth="jwt"``), which require exactly one."""
        domain = super()._get_validator_by_name_domain(validator_name)
        if not validator_name:
            domain = expression.AND(
                [domain, [("user_id_strategy", "!=", "oauth_server")]]
            )
        return domain

    def _get_uid(self, payload):
        if self.user_id_strategy != "oauth_server":
            return super()._get_uid(payload)
        authorization = self.env["oauth.server.authorization"].sudo()
        return authorization._get_for_access_token(self, payload).user_id.id
