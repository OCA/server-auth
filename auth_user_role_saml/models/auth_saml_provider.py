# Copyright 2026 360ERP (<https://www.360erp.com>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AuthSamlProvider(models.Model):
    _inherit = "auth.saml.provider"

    def _default_strict_sync(self):
        # Fetch the global parameter, defaulting to 'True'
        param = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("auth_user_role.strict_sync", "True")
        )
        return param == "True"

    sync_roles_strictly = fields.Boolean(
        string="Strict Role Synchronization",
        default=_default_strict_sync,
        help="If checked, any Odoo roles manually assigned to the user will be removed "
        "if they are not explicitly provided by the SAML IdP payload.",
    )

    def _hook_validate_auth_response(self, response, matching_value):
        """Extract the identity payload before the response object is destroyed."""
        vals = super()._hook_validate_auth_response(response, matching_value) or {}
        vals["saml_identity_payload"] = response.get_identity()
        return vals
