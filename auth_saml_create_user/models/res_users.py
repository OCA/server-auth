# © 2019 Savoir-faire Linux
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
import random

from odoo import models

_logger = logging.getLogger(__name__)
s = "abcdefghijklmnopqrstuvwxyz034567890ABCDEFGHIJKLMNOPQRSTUVWXYZ!@#$%^&*()?"
passlen = 16


class ResUsers(models.Model):
    _inherit = "res.users"

    def _auth_saml_signin(self, provider: int, validation: dict, saml_response) -> str:
        saml_uid = validation["user_id"]
        user_ids = self.env["res.users.saml"].search(
            [("saml_uid", "=", saml_uid), ("saml_provider_id", "=", provider)]
        )
        if self.check_if_create_user(provider) and not user_ids:
            self.create_user(saml_uid, provider)
        return super()._auth_saml_signin(provider, validation, saml_response)

    def check_if_create_user(self, provider):
        return self.env["auth.saml.provider"].browse(provider).create_user

    def create_user(self, saml_uid, provider):
        _logger.debug('Creating new Odoo user "%s" from SAML' % saml_uid)
        SudoUser = self.env["res.users"].sudo()
        new_user = SudoUser.create(
            {
                "name": saml_uid,
                "login": saml_uid,
                "password": "".join(random.sample(s, passlen)),
                "company_id": self.env["res.company"].sudo().browse(1).id,
            }
        )
        _logger.debug('Odoo user  "%s" created' % saml_uid)
        vals = {
            "saml_provider_id": provider,
            "saml_uid": saml_uid,
            "user_id": new_user.id,
        }
        saml = elf.env["res.users.saml"].create(vals)

        # Note: we need to commit to database because otherwise in phase of the first login
        # the user obtain: "You do not have access to this database. Please contact support."
        self.env.cr.commit()
