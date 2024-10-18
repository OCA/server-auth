# Copyright 2024 XCG Consulting <https://xcg-consulting.fr>
# License: AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import fields, models


class AuthOauthProvider(models.Model):
    _inherit = "auth.oauth.provider"

    autoredirect = fields.Boolean(
        "Automatic Redirection",
        default=False,
        help="Only the provider with the higher priority will be automatically "
        "redirected",
    )
