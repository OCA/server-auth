# Copyright 2023 Foodles
# @author: Pierre Verkest <pierreverkest84@gmail.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).


from odoo import models, fields


class ResUsersAPIKeys(models.Model):
    _inherit = "res.users.apikeys"
    
    scope = fields.Char(readonly=False)
