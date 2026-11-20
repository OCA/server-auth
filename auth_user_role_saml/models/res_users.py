# Copyright 2026 360ERP (<https://www.360erp.com>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from odoo import models

_logger = logging.getLogger(__name__)


class ResUser(models.Model):
    _inherit = "res.users"

    def _auth_saml_signin(self, provider, validation, saml_response):
        """
        Intercept the standard SAML sign-in, allow it to complete,
        and then pass the identity payload to the generic role engine.
        """
        login = super()._auth_saml_signin(provider, validation, saml_response)
        identity_payload = validation.get("saml_identity_payload")

        if identity_payload is not None:
            user = self.env["res.users"].sudo().search([("login", "=", login)], limit=1)

            if user:
                # Fetch the provider record to check its specific strict_sync setting
                provider_record = self.env["auth.saml.provider"].browse(provider)
                strict_sync = provider_record.sync_roles_strictly

                # If strict_sync is True but the database has NO mappings,
                # applying it will inadvertently wipe all roles from the logging-in user
                if strict_sync and not self.env[
                    "auth.user.role.mapping"
                ].sudo().search_count([], limit=1):
                    strict_sync = False

                # Pass strict_sync to the evaluation engine
                user.sudo().evaluate_and_apply_auth_roles(
                    identity_payload, strict_sync=strict_sync
                )

        return login
