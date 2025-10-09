# Copyright 2021 ACSONE SA/NV <https://acsone.eu>

from odoo import api, models


class ResUsers(models.Model):
    _inherit = "res.users"

    @api.model
    def _generate_signup_values(self, provider, validation, params):
        res = super()._generate_signup_values(provider, validation, params)
        if "login" in validation:
            res["login"] = validation["login"]
        return res
