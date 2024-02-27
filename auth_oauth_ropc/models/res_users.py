# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models
from odoo.exceptions import AccessDenied


class ResUsers(models.Model):

    _inherit = "res.users"

    def _check_credentials(self, password, env):
        try:
            return super(ResUsers, self)._check_credentials(password, env)
        except AccessDenied:
            passwd_allowed = (
                env["interactive"] or not self.env.user._rpc_api_keys_only()
            )
            if passwd_allowed and self.env.user.active:
                if ropc_provider := self.env["oauth.ropc.provider"].sudo().search([]):
                    if ropc_provider._authenticate(self.env.user.login, password):
                        return
            raise
