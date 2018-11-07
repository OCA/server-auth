# Copyright 2018 Brainbean Apps
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import logging
from odoo import fields, models

_logger = logging.getLogger(__name__)


class LdapGroupMapping(models.Model):
    _name = 'ldap.group.mapping'
    _description = 'LDAP group mapping'

    ldap_id = fields.Many2one(
        string='LDAP configuration',
        comodel_name='res.company.ldap',
    )
    regexp = fields.Char(
        string='RegExp',
        required=True,
        default='^cn=group,dc=example,dc=org$',
    )
    group_ids = fields.Many2many(
        'res.groups',
        'rel_ldap_group_mapping_groups',
        'ldap_group_mapping_id',
        'group_id',
        string='Groups',
    )
