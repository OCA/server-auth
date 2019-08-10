# Copyright 2019 Brainbean Apps (https://brainbeanapps.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class ResCompanyLdapGroup(models.Model):
    _name = 'res.company.ldap.group'
    _description = 'Company LDAP Group'

    company_ldap_id = fields.Many2one(
        string='Company LDAP',
        comodel_name='res.company.ldap',
        ondelete='cascade',
        required=True,
    )
    dn = fields.Char(
        string='Distinguished Name',
        required=True,
    )
    name = fields.Char(
        required=True,
    )
    mapping_ids = fields.One2many(
        string='Mappings',
        comodel_name='res.company.ldap.group.mapping',
        inverse_name='ldap_group_id',
    )

    _sql_constraints = [
        (
            'dn_company_uniq',
            'UNIQUE(company_ldap_id, dn)',
            'DN must be unique!'
        ),
    ]
