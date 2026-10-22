# Copyright 2026 spomata
# License: AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import fields, models


class AuthOauthProvider(models.Model):
    _inherit = "auth.oauth.provider"

    link_user_by_verified_email = fields.Boolean(
        string="Link Existing Users by Verified Email",
        help="On the first login of a subject unknown to Odoo, link it to the "
        "existing user whose login is the email claim, provided "
        "the provider asserts email_verified. The match must be unique, the "
        "user must not be linked yet and must not be a Settings administrator. "
        "Once linked, the user is identified by the subject only.",
    )
