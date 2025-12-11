# © 2021 Florian Kantelberg - initOS GmbH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class VaultTag(models.Model):
    _name = "vault.tag"
    _description = "Vault tag"
    _order = "name"

    name = fields.Char(required=True)

    _sql_constraints = [
        ("name_uniq", "unique(name)", "The tag must be unique!"),
    ]
