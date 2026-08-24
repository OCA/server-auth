# Copyright 2026 KOBROS-TECH LTD <https://www.kobros-tech.com>
# License: AGPL-3.0 or later (http://www.gnu.org)

from odoo import fields, models


class AuthOauthProvider(models.Model):
    _inherit = "auth.oauth.provider"

    flow = fields.Selection(
        selection_add=[
            ("access_token_code", "OAuth2 (Authorization Code Flow)"),
        ],
        ondelete={"access_token_code": "set default"},
        string="Auth Flow",
        required=True,
        default="access_token",
    )
