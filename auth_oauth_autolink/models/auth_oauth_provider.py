# Copyright 2026 Nimarosa
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AuthOauthProvider(models.Model):
    _inherit = "auth.oauth.provider"

    autolink_by_email = fields.Boolean(
        string="Auto-link existing users by email",
        default=False,
        help="On the first login through this provider, link the OAuth account "
        "to the existing user whose login is the e-mail address the provider "
        "verified. Administrators and users already linked to an OAuth "
        "account are never linked.\n"
        "Only enable this for providers you trust to verify e-mail ownership "
        "(e.g. Google Workspace).",
    )
