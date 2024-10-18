# Copyright 2021 Camptocamp SA
# @author: Simone Orsi <simone.orsi@camptocamp.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).


from odoo import fields, models


class AuthApiKeyGroup(models.Model):
    """Group API keys together."""

    _name = "auth.api.key.group"
    _description = "API Key auth group"

    name = fields.Char(required=True)
    code = fields.Char(required=True)
    auth_api_key_ids = fields.Many2many(
        comodel_name="auth.api.key",
        relation="auth_api_key_group_rel",
        column1="group_id",
        column2="key_id",
        string="API Keys",
    )
