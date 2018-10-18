# Copyright (C) 2018 Brainbean Apps
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import logging
from odoo import fields, api, models

_logger = logging.getLogger(__name__)


class LdapAttributeMapping(models.Model):
    _name = 'ldap.attribute.mapping'
    _description = 'LDAP attribute mapping'

    ldap_id = fields.Many2one(
        string='LDAP configuration',
        comodel_name='res.company.ldap',
    )
    attribute_name = fields.Char(
        string='Attribute',
        required=True,
        help='LDAP attribute name from where value is taken',
    )
    field_name = fields.Selection(
        string='Mapped field',
        selection='_field_name_selection',
        required=True,
        help='Entity field to where value is written',
    )
    mode = fields.Selection(
        string='Sync mode',
        selection='_mode_selection',
        required=True,
        help='Defines mode of synchronization',
    )

    @api.model
    def _field_name_selection(self):
        fields = self.env['res.users'].fields_get().items()

        def valid_field(f, d):
            return d.get('type') == 'char' and not d.get('readonly')
        result = [(f, d.get('string')) for f, d in fields if valid_field(f, d)]

        _logger.info('Mappable fields: %s', result)

        return result

    @api.model
    def _mode_selection(self):
        return [
            ('initial', 'On user creation'),
            ('always', 'On every login')
        ]
