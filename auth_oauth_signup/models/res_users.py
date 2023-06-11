# Copyright 2023 Paja SIA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, models

from odoo.addons.auth_signup.models.res_partner import SignupError


class ResUsers(models.Model):
    _inherit = "res.users"

    @api.model
    def _signup_create_user(self, values):
        provider = False
        oauth_fields = {"oauth_provider_id", "oauth_uid", "oauth_access_token"}
        if values.keys() & oauth_fields and all(
            values[oauth_field] for oauth_field in oauth_fields
        ):
            provider = self.env["auth.oauth.provider"].browse(
                values["oauth_provider_id"]
            )

        try:
            new_user = super(ResUsers, self)._signup_create_user(values)
        except SignupError as e:
            # Slightly dirty, but still cleaner than creating two separate modules
            # for different scenarios based on whether "website" is installed or not.
            # The method `_get_signup_invitation_scope` in "website" gets to run first
            # (unless this module had a dependency to it) and thus never calls super,
            # so overriding that method would only work if "website" wasn't installed.
            if provider and provider.allow_signup:
                new_user = self._create_user_from_template(values)
            else:
                raise e

        return new_user
