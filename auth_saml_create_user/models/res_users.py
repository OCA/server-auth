# © 2019 Savoir-faire Linux
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
import random

from odoo import models
from odoo.tools import safe_eval

from odoo.addons.auth_saml.models.ir_config_parameter import ALLOW_SAML_UID_AND_PASSWORD

_logger = logging.getLogger(__name__)
s = "abcdefghijklmnopqrstuvwxyz034567890ABCDEFGHIJKLMNOPQRSTUVWXYZ!@#$%^&*()?"
passlen = 16


class ResUsers(models.Model):
    _inherit = "res.users"

    def check_if_create_user(self, provider):
        return self.env["auth.saml.provider"].browse(provider).create_user

    def create_user(self, saml_uid, provider):
        _logger.debug(f"Creating new Odoo user {saml_uid} from SAML")
        SudoUser = self.env["res.users"].sudo()
        values = {
            "name": saml_uid,
            "login": saml_uid,
            "saml_ids": [
                (0, 0, {"saml_provider_id": provider, "saml_uid": saml_uid}),
            ],
            "company_id": self.env["res.company"].sudo().browse(1).id,
        }
        allow_saml_password = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param(ALLOW_SAML_UID_AND_PASSWORD, "False")
        )
        if safe_eval.safe_eval(allow_saml_password):
            values["password"] = "".join(random.sample(s, passlen))
        res = SudoUser.create(values)
        return res

    def _auth_saml_signin(self, provider: int, validation: dict, saml_response) -> str:
        """
        Overload to auto create a new user if configured to allow it.
        """
        saml_uid = validation["user_id"]
        user_ids = self.env["res.users.saml"].search(
            [("saml_uid", "=", saml_uid), ("saml_provider_id", "=", provider)]
        )
        if self.check_if_create_user(provider) and not user_ids:
            self.create_user(saml_uid, provider)
        return super()._auth_saml_signin(provider, validation, saml_response)
