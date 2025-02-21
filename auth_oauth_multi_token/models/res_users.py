# Copyright 2016 Florent de Labarre
# Copyright 2017 Camptocamp
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
import uuid

from odoo import api, exceptions, fields, models


class ResUsers(models.Model):
    _inherit = "res.users"

    def _generate_oauth_master_uuid(self):
        return uuid.uuid4().hex

    oauth_access_token_ids = fields.One2many(
        comodel_name="auth.oauth.multi.token",
        inverse_name="user_id",
        string="OAuth Tokens",
        copy=False,
        readonly=True,
        groups="base.group_system",
    )
    oauth_access_max_token = fields.Integer(
        string="Max Number of Simultaneous Connections", default=10, required=True
    )

    # use the oauth_access_token field as oauth_master_uuid
    oauth_access_token = fields.Char(
        required=True,
        default=lambda self: self._generate_oauth_master_uuid(),
    )

    @property
    def multi_token_model(self):
        return self.env["auth.oauth.multi.token"]

    @api.model
    def _generate_signup_values(self, provider, validation, params):
        """Because access_token was replaced in
        _auth_oauth_signin we need to replace it here."""
        res = super()._generate_signup_values(provider, validation, params)
        res["oauth_access_token"] = params["access_token_multi"]
        return res

    @api.model
    def _auth_oauth_signin(self, provider, validation, params):
        """Override to handle sign-in with multi token."""
        params["access_token_multi"] = params["access_token"]

        # Lookup for user by oauth uid and provider
        oauth_uid = validation["user_id"]
        user = self.search(
            [("oauth_uid", "=", oauth_uid), ("oauth_provider_id", "=", provider)]
        )

        # Because access_token is automatically written to the user, we need to replace
        # this by the existing oauth_access_token which acts as oauth_master_uuid
        params["access_token"] = user.oauth_access_token
        res = super()._auth_oauth_signin(provider, validation, params)

        if not user:
            raise exceptions.AccessDenied()
        user.ensure_one()
        # user found and unique: create a token
        self.multi_token_model.create(
            {"user_id": user.id, "oauth_access_token": params["access_token_multi"]}
        )
        return res

    def action_oauth_clear_token(self):
        """Inactivate current user tokens."""
        self.mapped("oauth_access_token_ids")._oauth_clear_token()
        for res in self:
            res.oauth_access_token = self._generate_oauth_master_uuid()

    @api.model
    def _check_credentials(self, credential, env):
        """Override to check credentials against multi tokens."""
        try:
            return super()._check_credentials(credential, env)
        except exceptions.AccessDenied:
            passwd_allowed = (
                env["interactive"] or not self.env.user._rpc_api_keys_only()
            )
            if passwd_allowed and self.env.user.active and "token" in credential:
                res = self.multi_token_model.sudo().search(
                    [
                        ("user_id", "=", self.env.uid),
                        ("oauth_access_token", "=", credential["token"]),
                    ]
                )
                if res:
                    return {
                        "uid": self.env.user.id,
                        "auth_method": "oauth",
                        "mfa": "default",
                    }

            raise
