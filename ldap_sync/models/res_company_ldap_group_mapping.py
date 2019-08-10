# Copyright 2019 Brainbean Apps (https://brainbeanapps.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class ResCompanyLdapGroupMapping(models.Model):
    _name = 'res.company.ldap.group.mapping'
    _description = 'Company LDAP Group mapping'
    _order = 'sequence, id'

    sequence = fields.Integer(
        default=10,
    )
    company_ldap_id = fields.Many2one(
        string='Company LDAP',
        comodel_name='res.company.ldap',
        ondelete='cascade',
        required=True,
    )
    ldap_group_id = fields.Many2one(
        string='LDAP Group',
        comodel_name='res.company.ldap.group',
    )
    odoo_group_ids = fields.Many2many(
        string='Odoo Groups',
        comodel_name='res.groups',
    )

    _sql_constraints = [
        (
            'ldap_group_company_uniq',
            'UNIQUE(company_ldap_id, ldap_group_id)',
            'Only one mapping per LDAP Group!'
        ),
    ]
