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

    @api.multi
    def _get_user_groups(self, user_id, attrs):
        groups = []
        user = self.env['res.users'].browse(user_id)

        if self.only_saml_groups:
            _logger.debug('deleting all groups from user %d', user_id)
            groups.append((5, False, False))

        for mapping in self.group_mapping_ids:
            operator = self.env['auth.saml.provider.operator']
            operator = getattr(operator, mapping.operator)
            _logger.debug('checking mapping %s', mapping)
            if operator(attrs, mapping):
                _logger.debug(
                    'adding user %d to group %s', user, mapping.group_id.name,
                )
                groups.append((4, mapping.group_id.id, False))

        user.write({
            'groups_id': groups
        })
