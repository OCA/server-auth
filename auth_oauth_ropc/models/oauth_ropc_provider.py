# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import requests

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class OAuthRopcProvider(models.Model):

    _name = "oauth.ropc.provider"
    _description = "OAuth ROPC Provider"

    name = fields.Char()
    client_id = fields.Char(string="Client ID")
    client_secret = fields.Char()
    auth_endpoint = fields.Char(string="Authorization URL", required=True)
    resource = fields.Char()
    scope = fields.Char()
    active = fields.Boolean(default=True)

    @api.constrains("active")
    def _check_active(self):
        records_to_check = self.filtered(lambda r: r.active)
        for record in records_to_check:
            if self.search([("id", "!=", record.id)]):
                raise ValidationError(_("""You can define only one active provider"""))

    def _authenticate(self, login, password):
        self.ensure_one()
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "resource": self.resource,
            "scope": self.scope,
            "grant_type": "password",
            "username": login,
            "password": password,
        }
        r = requests.post(self.auth_endpoint, data=data, timeout=5)
        if r.status_code == 200:
            return True
        return False
