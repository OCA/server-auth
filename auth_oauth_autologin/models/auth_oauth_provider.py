# Copyright 2021 ACSONE SA/NV <https://acsone.eu>
# License: AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import fields, models


class AuthOauthProvider(models.Model):
    _inherit = "auth.oauth.provider"

    autologin = fields.Boolean(
        string="Automatic Login",
        help=(
            "If exactly one enabled provider has this checked, "
            "the login screen redirects to the OAuth provider."
        ),
    )

    login_url_without_oauth = fields.Text(
        string="Login Url without Oauth",
        help=(
            "Url used for login without Oauth Method."
        )
    )
