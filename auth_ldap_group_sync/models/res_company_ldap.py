# Copyright 2018 Brainbean Apps
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import logging
import re
from odoo import fields, api, models, registry, tools, SUPERUSER_ID

_logger = logging.getLogger(__name__)

try:
    import ldap
    from ldap.filter import filter_format
except (ImportError) as err:
    _logger.debug(err)


class ResCompanyLdap(models.Model):
    _inherit = 'res.company.ldap'

    sync_ldap_group_membership_periodically = fields.Boolean(
        string='Sync periodically',
        default=False,
    )
    ldap_group_membership_attribute = fields.Char(
        string='Membership attribute',
        required=True,
        default='memberOf',
        help='The attribute field to use when loading a user\'s groups',
    )
    only_ldap_group_membership = fields.Boolean(
        string='Only LDAP group membership',
        default=True,
        help='Respect only LDAP group membership',
    )
    ldap_group_mapping_ids = fields.One2many(
        string='LDAP group mapping',
        comodel_name='ldap.group.mapping',
        inverse_name='ldap_id',
    )

    def _map_ldap_groups(self, ldap_entry):
        attribute_values = list(map(
            lambda x: x.decode(),
            ldap_entry[1][self.ldap_group_membership_attribute]
        ))

        group_ids = []
        for mapping in self.ldap_group_mapping_ids:
            regexp = re.compile(mapping.regexp)
            if not any(map(lambda x: regexp.match(x), attribute_values)):
                continue

            group_ids.extend(mapping.group_ids.ids)
            for group_id in mapping.group_ids:
                group_ids.extend(group_id.trans_implied_ids.ids)

        return group_ids

    def _get_user_group_ids(self, group_ids):
        if self.only_ldap_group_membership:
            return [(6, False, group_ids)]

        return list(map(lambda x: (4, x, False), group_ids))

    def _update_group_membership(self, user):
        ldap_entry = False
        try:
            filter = filter_format(self.ldap_filter, (user.login,))
        except TypeError:
            _logger.warning((
                'Could not format LDAP filter. '
                'Your filter should contain one \'%s\'.'
            ))
            return False
        try:
            results = self._query(self, tools.ustr(filter))

            # Get rid of (None, attrs) for searchResultReference replies
            results = [i for i in results if i[0]]
            if len(results) == 1:
                ldap_entry = results[0]
        except ldap.LDAPError as e:
            _logger.error('An LDAP exception occurred: %s', e)
            raise e
        if not ldap_entry:
            return ldap_entry

        groups = self._map_ldap_groups(ldap_entry)

        if (
            not self.only_ldap_group_membership and
                groups not in user.groups_id.ids
        ) or (
            self.only_ldap_group_membership and
                set(groups) != set(user.groups_id.ids)
        ):
            _logger.info(
                'Updating group membership for login "%s"',
                user.login
            )

            with registry(self.env.cr.dbname).cursor() as cr:
                env = api.Environment(cr, SUPERUSER_ID, {})

                SudoUser = env['res.users'].sudo()
                SudoUser.browse(user.id).write({
                    'groups_id': self._get_user_group_ids(groups),
                })
        else:
            _logger.info(
                'Group membership for login "%s" is up to date',
                user.login
            )

        return ldap_entry

    def _map_ldap_attributes(self, conf, login, ldap_entry):
        fields = super()._map_ldap_attributes(
            conf,
            login,
            ldap_entry
        )

        _logger.info(
            'Setting group membership from LDAP for login "%s"',
            login
        )

        ldap = self.env['res.company.ldap'].sudo().browse(conf['id'])
        groups = ldap._map_ldap_groups(ldap_entry)
        fields.update({
            'groups_id': ldap._get_user_group_ids(groups),
        })

        return fields

    def _sync_group_membership(self):
        ldap_configs = self.search([
            ('sync_ldap_group_membership_periodically', '=', True),
            ('ldap_server', '!=', False),
        ], order='sequence')

        users = self.env['res.users'].search([
            (1, '=', 1),
        ])

        _logger.info(
            'Syncing group membership of %d users from %d LDAP servers',
            len(users),
            len(ldap_configs)
        )

        for user in users:
            for ldap_config in ldap_configs:
                ldap_entry = ldap_config._update_group_membership(user)
                if not ldap_entry:
                    continue

                _logger.info(
                    (
                        'Group membership of "%s" is in sync with LDAP groups'
                        ' from "%s:%s"'
                    ),
                    user.login,
                    ldap_config.ldap_server,
                    ldap_config.ldap_server_port
                )

                break
