# Copyright 2021 Camptocamp SA
# @author: Simone Orsi <simone.orsi@camptocamp.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).


from odoo import fields, models


class AuthApiKey(models.Model):
    _inherit = "auth.api.key"

    auth_api_key_group_ids = fields.Many2many(
        comodel_name="auth.api.key.group",
        relation="auth_api_key_group_rel",
        column1="key_id",
        column2="group_id",
        string="Auth Groups",
    )
