# Copyright (C) 2022 XCG Consulting <https://xcg-consulting.fr/>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging

from odoo import api, models

_logger = logging.getLogger(__name__)
ALLOW_SAML_UID_AND_PASSWORD = "auth_saml.allow_saml_uid_and_internal_password"


class IrConfigParameter(models.Model):
    """Redefined to update users when our parameter is changed."""

    _inherit = "ir.config_parameter"

    @api.model_create_multi
    def create(self, vals_list):
        """Redefined to update users when our parameter is changed."""
        result = super().create(vals_list)
        if result.filtered(lambda param: param.key == ALLOW_SAML_UID_AND_PASSWORD):
            self.env["res.users"].allow_saml_and_password_changed()
        return result

    def write(self, vals):
        """Redefined to update users when our parameter is changed."""
        result = super().write(vals)
        if self.filtered(lambda param: param.key == ALLOW_SAML_UID_AND_PASSWORD):
            self.env["res.users"].allow_saml_and_password_changed()
        return result

    def unlink(self):
        """Redefined to update users when our parameter is deleted."""
        param_saml = self.filtered(
            lambda param: param.key == ALLOW_SAML_UID_AND_PASSWORD
        )
        result = super().unlink()
        if result and param_saml:
            self.env["res.users"].allow_saml_and_password_changed()
        return result
