# Copyright 2016 Florent de Labarre
# Copyright 2017 Camptocamp
# Copyright 2021 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import api, fields, models


class AuthOauthMultiToken(models.Model):
    """Define a set of tokens."""

    _name = "auth.oauth.multi.token"
    _description = "OAuth2 token"
    _order = "id desc"

    oauth_access_token = fields.Char(
        string="OAuth Access Token", readonly=True, copy=False
    )
    user_id = fields.Many2one(
        comodel_name="res.users",
        string="User",
        required=True,
        readonly=True,
        index=True,
        ondelete="cascade",
    )

    @api.model
    def create(self, vals):
        """Override to validate tokens."""
        token = super().create(vals)
        token._oauth_validate_multi_token()
        return token

    @api.model
    def _oauth_user_tokens(self, user_id):
        """Retrieve tokens for given user.

        :param user_id: Odoo ID of the user
        """
        return self.search([("user_id", "=", user_id)])

    def _oauth_validate_multi_token(self):
        """Check current user's token and clear them if max number reached."""
        user_tokens = self._oauth_user_tokens(self.user_id.id)
        max_token = self.user_id.oauth_access_max_token
        if user_tokens and len(user_tokens) > max_token:
            # clear last token
            user_tokens[max_token - 1]._oauth_clear_token()

    def _oauth_clear_token(self):
        """Disable current token records."""
        self.unlink()
