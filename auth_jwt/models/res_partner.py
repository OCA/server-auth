from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    created_by_jwt = fields.Boolean("Created by JWT", default=False)
    auth_jwt_email = fields.Char("Auth JWT Email")
