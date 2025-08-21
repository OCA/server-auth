# Copyright 2025 Alberto Martínez <alberto.martinez@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class APIKeys(models.Model):
    _inherit = "res.users.apikeys"

    def _generate(self, scope, name):
        new_scope = self.env.context.get("apikey_scope")
        scope = new_scope if new_scope else scope
        return super()._generate(scope, name)
