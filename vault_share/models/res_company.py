# © 2021 Florian Kantelberg - initOS GmbH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class RecCompany(models.Model):
    _inherit = "res.company"

    vault_share_delay = fields.Integer(default=0)
