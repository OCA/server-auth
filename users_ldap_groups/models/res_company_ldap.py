# Copyright 2012-2018 Therp BV <https://therp.nl>
# Copyright 2018 Brainbean Apps <https://brainbeanapps.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from logging import getLogger
from odoo import api, fields, models
_logger = getLogger(__name__)


class ResCompanyLdap(models.Model):
    _inherit = 'res.company.ldap'

    group_mapping_ids = fields.One2many(
        'res.company.ldap.group_mapping',
        'ldap_id',
        'Group mappings',
        help='Define how Odoo groups are assigned to LDAP users',
    )
    only_ldap_groups = fields.Boolean(
        'Only LDAP groups',
        default=False,
        help=(
            'If this is checked, manual changes to group membership are '
            'undone on every login (so Odoo groups are always synchronous '
            'with LDAP groups). If not, manually added groups are preserved.'
        ),
    )

    @api.model
    def _get_or_create_user(self, conf, login, ldap_entry):
        op_obj = self.env['res.company.ldap.operator']
        user_id = super()._get_or_create_user(
            conf, login, ldap_entry
        )
        if not user_id:
            return user_id
        this = self.browse(conf['id'])
        user = self.env['res.users'].browse(user_id)

        groups = []

        if this.only_ldap_groups:
            _logger.debug('deleting all groups from user %d', user_id)
            groups.append((5, False, False))

        for mapping in this.group_mapping_ids:
            operator = getattr(op_obj, mapping.operator)
            _logger.debug('checking mapping %s', mapping)

            if operator(ldap_entry, mapping):
                _logger.debug(
                    'adding user %d to group %s', user, mapping.group_id.name,
                )
                groups.append((4, mapping.group_id.id, False))

        user.write({
            'groups_id': groups
        })

        return user_id
