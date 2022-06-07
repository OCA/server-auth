# Copyright (C) 2022 XCG Consulting <https://xcg-consulting.fr/>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging

from odoo import api, models
from .base_settings import _SAML_UID_AND_PASS_SETTING

_logger = logging.getLogger(__name__)


class IrConfigParameter(models.Model):
    """Redefined to update users when our parameter is changed."""

    _inherit = "ir.config_parameter"

    @api.model
    def create(self, vals):
        """Redefined to update users when our parameter is changed."""
        result = super().create(vals)
        if result.filtered(
            lambda param: param.key == _SAML_UID_AND_PASS_SETTING
        ):
            self.env["res.users"].allow_saml_and_password_changed()
        return result

    def write(self, vals):
        """Redefined to update users when our parameter is changed."""
        result = super().write(vals)
        if self.filtered(
            lambda param: param.key == _SAML_UID_AND_PASS_SETTING
        ):
            self.env["res.users"].allow_saml_and_password_changed()
        return result
