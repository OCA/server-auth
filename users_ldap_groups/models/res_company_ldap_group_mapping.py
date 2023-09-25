# Copyright 2012-2018 Therp BV <https://therp.nl>
# Copyright 2018 Brainbean Apps <https://brainbeanapps.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import fields, models


class ResCompanyLdapGroupMapping(models.Model):
    _name = "res.company.ldap.group_mapping"
    _description = "LDAP group mapping"
    _rec_name = "ldap_attribute"
    _order = "ldap_attribute"

    ldap_id = fields.Many2one(
        "res.company.ldap",
        "LDAP server",
        required=True,
        ondelete="cascade",
    )
    ldap_attribute = fields.Char(
        "LDAP attribute",
        help=("The LDAP attribute to check.\nFor active directory, use memberOf."),
    )
    operator = fields.Selection(
        lambda self: [
            (o, o) for o in self.env["res.company.ldap.operator"].operators()
        ],
        help=(
            "The operator to check the attribute against the value\n"
            "For active directory, use 'contains'"
        ),
        required=True,
    )
    value = fields.Char(
        help=(
            "The value to check the attribute against.\n"
            "For active directory, use the dn of the desired group"
        ),
        required=True,
    )
    group_id = fields.Many2one(
        "res.groups", "Odoo group", help="The Odoo group to assign", required=True
    )
