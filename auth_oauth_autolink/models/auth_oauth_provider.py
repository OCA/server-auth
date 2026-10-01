# Copyright 2026 Nimarosa
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AuthOauthProvider(models.Model):
    _inherit = "auth.oauth.provider"

    autolink_by_email = fields.Boolean(
        string="Auto-link existing users by email",
        default=False,
        help="On the first login through this provider, link the OAuth account "
        "to the existing Odoo user whose login is the same e-mail address, "
        "instead of refusing the login.\n"
        "The link is only performed when the provider itself reports the "
        "e-mail as verified, when exactly one active user matches, and when "
        "that user is not linked to any OAuth account yet.\n"
        "Only enable this for providers you trust to verify e-mail ownership "
        "(e.g. Google Workspace).",
    )
