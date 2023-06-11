# Copyright 2023 Paja SIA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import fields, models


class AuthOauthProvider(models.Model):
    _inherit = "auth.oauth.provider"

    allow_signup = fields.Boolean(
        default=False,
        help=(
            "When enabled, new users logging in through this provider for the first time "
            "are allowed to sign up, even when the global sign up is disabled."
        ),
    )
