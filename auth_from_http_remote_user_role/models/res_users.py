# Copyright 2018 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import fields, models


class ResUsers(models.Model):
    _inherit = 'res.users'

    last_http_header_roles = fields.Char(
        string='Last HTTP header roles'
    )
