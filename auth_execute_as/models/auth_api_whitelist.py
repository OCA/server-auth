# Copyright 2026 Kencove (https://www.kencove.com).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class AuthApiWhitelist(models.Model):
    _name = "auth.api.whitelist"
    _description = "API Whitelist"

    name = fields.Char(required=True)
    description = fields.Text()
    line_ids = fields.One2many(
        comodel_name="auth.api.whitelist.line",
        inverse_name="whitelist_id",
        string="Whitelist Lines",
    )
