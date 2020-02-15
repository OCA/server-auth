# © 2019 Savoir-faire Linux
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields, models, api

import logging

_logger = logging.getLogger(__name__)


class AuthSamlProvider(models.Model):
    _inherit = ['auth.saml.provider']

    group_mapping_ids = fields.One2many(
        'auth.saml.provider.group_mapping',
        'saml_id',
        'Group mappings',
        help='Define how Odoo groups are assigned to SAML users',
    )
    only_saml_groups = fields.Boolean(
        'Only SAML groups',
        default=False,
        help=(
            'If this is checked, manual changes to group membership are '
            'undone on every login (so Odoo groups are synchronous on login'
            'with SAML groups). If not, manually added groups are preserved.'
        ),
    )
    create_user_if_mapping = fields.Boolean(
        'User creation depends on group mapping',
        default=False,
        help=(
            'If this is checked, only users with at least one group mapping'
            'will be created.'
        ),
    )

    @api.multi
    def _get_user_groups(self, user_id, attrs):
        groups = []
        user = self.env['res.users'].browse(user_id)

        if self.only_saml_groups:
            _logger.debug('deleting all groups from user %d', user_id)
            groups.append((5, False, False))

        groups += self._get_group_mappings(attrs)
        user.write({
            'groups_id': groups
        })

    def _get_group_mappings(self, attrs):
        groups = []
        for mapping in self.group_mapping_ids:
            operator = self.env['auth.saml.provider.operator']
            operator = getattr(operator, mapping.operator)
            _logger.debug('checking mapping %s', mapping)
            if operator(attrs, mapping):
                groups.append((4, mapping.group_id.id, False))
        return groups