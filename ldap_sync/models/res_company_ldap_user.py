# Copyright 2019 Brainbean Apps (https://brainbeanapps.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class ResCompanyLdapUser(models.Model):
    _name = 'res.company.ldap.user'
    _description = 'Company LDAP User'

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
    login = fields.Char(
        required=True,
    )
    email = fields.Char(
        required=True,
    )
    name = fields.Char(
        required=True,
    )
    unique_identifier = fields.Char(
        required=True,
    )
    ldap_group_ids = fields.Many2many(
        string='LDAP Groups',
        comodel_name='res.company.ldap.group',
    )

    _sql_constraints = [
        (
            'dn_company_uniq',
            'UNIQUE(company_ldap_id, dn)',
            'DN must be unique!'
        ),
        (
            'login_company_uniq',
            'UNIQUE(company_ldap_id, login)',
            'Login must be unique!'
        ),
        (
            'unique_identifier_company_uniq',
            'UNIQUE(company_ldap_id, unique_identifier)',
            'Unique Identifier must be unique!'
        ),
    ]
