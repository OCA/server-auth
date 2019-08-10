# Copyright 2019 Brainbean Apps (https://brainbeanapps.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import ldap
import logging

from odoo import fields, api, models, tools
from odoo.tools.pycompat import to_text

_logger = logging.getLogger(__name__)


class ResCompanyLdap(models.Model):
    _inherit = 'res.company.ldap'

    scheduled_sync_enabled = fields.Boolean()
    login_sync_enabled = fields.Boolean()
    sync_group_membership = fields.Boolean()
    users_base_dn = fields.Char(
        default='cn=users,cn=accounts,dc=example,dc=org',
    )
    user_object_filter = fields.Char(
        default='(objectclass=inetorgperson)',
    )
    user_login_attribute = fields.Char(
        default='uid',
    )
    user_email_attribute = fields.Char(
        default='mail',
    )
    user_name_attribute = fields.Char(
        default='cn',
    )
    user_unique_identifier_attribute = fields.Char(
        default='objectGUID',
    )
    user_group_membership_attribute = fields.Char(
        default='memberOf',
    )
    deactivate_unlinked_users = fields.Boolean(
        default=True,
    )
    deactivate_non_ldap_users = fields.Boolean(
        default=False,
    )
    ignore_non_ldap_user_ids = fields.Many2many(
        comodel_name='res.users',
    )
    groups_base_dn = fields.Char(
        default='cn=groups,cn=accounts,dc=example,dc=org',
    )
    group_object_filter = fields.Char(
        default='(objectclass=groupOfNames)',
    )
    group_name_attribute = fields.Char(
        default='cn',
    )
    ldap_user_ids = fields.One2many(
        string='LDAP Users',
        comodel_name='res.company.ldap.user',
        inverse_name='company_ldap_id',
    )
    ldap_group_ids = fields.One2many(
        string='LDAP Groups',
        comodel_name='res.company.ldap.group',
        inverse_name='company_ldap_id',
    )
    ldap_group_mapping_ids = fields.One2many(
        string='LDAP Group Mappings',
        comodel_name='res.company.ldap.group.mapping',
        inverse_name='company_ldap_id',
    )

    @api.model
    def _scheduled_sync(self):
        try:
            self.search([('scheduled_sync_enabled', '=', True)]).with_context(
                scheduled=True,
            )._sync()
        except Exception as e:
            _logger.error(
                'Scheduled LDAP directory sync failed: %s',
                e
            )

    def _authenticate(self, conf, login, password):
        entry = super()._authenticate(conf, login, password)
        if not entry:
            return entry
        company_ldap = self.sudo().browse(conf['id'])
        if company_ldap.login_sync_enabled:
            # company_ldap._sync_single_user(entry[0])
            company_ldap._sync()
        return entry

    @api.multi
    def _sync(self):
        for server in self:
            server._sync_groups()
            server._sync_users()
            if server.sync_group_membership:
                server._sync_group_membership()

    @api.multi
    def _get_sync_query_config(self, base_dn):
        self.ensure_one()
        config = self._get_ldap_dicts()[0]
        config.update({
            'ldap_base': base_dn,
        })
        return config

    def _ldap_query(self, conf, filterstr, retrieve_attributes=None):
        """
        Replacement for _query() since it's impossible to figure out if the
        query has failed or returned nothing.
        """
        try:
            connection = self._connect(conf)
            ldap_password = conf['ldap_password'] or ''
            ldap_binddn = conf['ldap_binddn'] or ''
            connection.simple_bind_s(to_text(ldap_binddn), to_text(ldap_password))
            results = connection.search_st(
                to_text(conf['ldap_base']),
                ldap.SCOPE_SUBTREE,
                filterstr,
                retrieve_attributes,
                timeout=60,
            )
            connection.unbind()
            return results
        except ldap.INVALID_CREDENTIALS:
            _logger.error('LDAP bind failed.')
            return None
        except ldap.LDAPError as e:
            _logger.error('An LDAP exception occurred: %s', e)
            return None
        return None

    @api.multi
    def _get_sync_group_attribs(self):
        self.ensure_one()
        return [
            self.group_name_attribute,
        ]

    @api.multi
    def _prepare_ldap_group_values(self, dn, attribs):
        self.ensure_one()
        return {
            'dn': dn,
            'name': attribs[self.group_name_attribute][0].decode(),
        }

    @api.multi
    def _sync_groups(self):
        self.ensure_one()
        ResCompanyLdapGroup = self.env['res.company.ldap.group']
        results = self._ldap_query(
            self._get_sync_query_config(self.groups_base_dn),
            tools.ustr(self.group_object_filter),
            retrieve_attributes=self._get_sync_group_attribs(),
        )
        if results is None:
            _logger.error('LDAP query failed, aborting groups sync')
            return
        existing_group_ids = ResCompanyLdapGroup
        new_group_ids = []
        for entry in results:
            if not entry[0]:
                continue
            dn = entry[0]
            attribs = entry[1]
            group_id = ResCompanyLdapGroup.search(
                [
                    ('company_ldap_id', '=', self.id),
                    ('dn', '=', dn),
                ],
                limit=1,
            )
            if group_id:
                existing_group_ids |= group_id
            else:
                new_group_ids.append(
                    (0, False, self._prepare_ldap_group_values(dn, attribs))
                )
        self.ldap_group_ids = existing_group_ids
        self.ldap_group_ids = new_group_ids

    @api.multi
    def _get_sync_user_attribs(self):
        self.ensure_one()
        return [
            self.user_login_attribute,
            self.user_email_attribute,
            self.user_name_attribute,
            self.user_unique_identifier_attribute,
            self.user_group_membership_attribute,
        ]

    @api.multi
    def _prepare_ldap_user_values(self, dn, attribs):
        self.ensure_one()
        return {
            'dn': dn,
            'login': attribs[self.user_login_attribute][0].decode(),
            'email': attribs[self.user_email_attribute][0].decode(),
            'name': attribs[self.user_name_attribute][0].decode(),
            'unique_identifier': attribs[
                self.user_unique_identifier_attribute
            ][0].decode(),
            'ldap_group_ids': [(5, 0, 0)] + list(map(
                lambda ldap_group: (4, ldap_group.id, 0),
                self.ldap_group_ids.filtered(
                    lambda ldap_group: ldap_group.dn in list(map(
                        lambda x: x.decode(),
                        attribs[self.user_group_membership_attribute],
                    ))
                ),
            )),
        }

    @api.multi
    def _prepare_odoo_user_values(self, ldap_user):
        self.ensure_one()
        return {
            'login': ldap_user.login,
            'name': ldap_user.name,
            'email': ldap_user.email,
            'active': True,
        }

    @api.multi
    def _prepare_inactive_odoo_user_values(self, ldap_user):
        self.ensure_one()
        return {
            'ldap_user_id': False,
            'active': False,
        }

    @api.multi
    def _prepare_nonldap_odoo_user_values(self):
        self.ensure_one()
        return {
            'active': False,
        }

    @api.multi
    def _sync_users(self):
        self.ensure_one()
        ResCompanyLdapUser = self.env['res.company.ldap.user']
        ResUsers = self.env['res.users']
        results = self._ldap_query(
            self._get_sync_query_config(self.users_base_dn),
            tools.ustr(self.user_object_filter),
            retrieve_attributes=self._get_sync_user_attribs(),
        )
        if results is None:
            _logger.error('LDAP query failed, aborting users sync')
            return
        existing_user_ids = ResCompanyLdapUser
        new_user_ids = []
        for entry in results:
            if not entry[0]:
                continue
            dn = entry[0]
            attribs = entry[1]
            user_id = ResCompanyLdapUser.search(
                [
                    ('company_ldap_id', '=', self.id),
                    (
                        'unique_identifier',
                        '=',
                        attribs[
                            self.user_unique_identifier_attribute
                        ][0].decode(),
                    ),
                ],
                limit=1,
            )
            values = self._prepare_ldap_user_values(dn, attribs)
            if user_id:
                user_id.write(values)
                existing_user_ids |= user_id
            else:
                new_user_ids.append(
                    (0, False, values)
                )
        missing_user_ids = self.ldap_user_ids - existing_user_ids
        for ldap_user_id in missing_user_ids:
            odoo_user_id = ResUsers.with_context(active_test=False).search(
                [('ldap_user_id', '=', ldap_user_id.id)],
                limit=1,
            )
            if not odoo_user_id:
                continue
            if self.deactivate_unlinked_users and \
                    odoo_user_id not in self.ignore_non_ldap_user_ids and \
                    odoo_user_id != self.env.user:
                odoo_user_id.with_context(ldap_sync=True).sudo().write(
                    self._prepare_inactive_odoo_user_values(odoo_user_id)
                )
                odoo_user_id.sudo().unset_password()
        self.ldap_user_ids = existing_user_ids
        self.ldap_user_ids = new_user_ids
        new_user_ids = self.ldap_user_ids - existing_user_ids
        for ldap_user_id in new_user_ids:
            odoo_user_id = ResUsers.with_context(active_test=False).search(
                [('login', '=', ldap_user_id.login)],
                limit=1,
            )
            values = self._prepare_odoo_user_values(ldap_user_id)
            if not odoo_user_id:
                if self.user:
                    odoo_user_id = self.user.with_context(
                        no_reset_password=True,
                    ).sudo().copy(default=values)
                else:
                    odoo_user_id = ResUsers.with_context(
                        no_reset_password=True,
                    ).sudo().create(values)
            else:
                odoo_user_id.with_context(ldap_sync=True).sudo().write(
                    self._prepare_odoo_user_values(ldap_user_id),
                )
            odoo_user_id.sudo().ldap_user_id = ldap_user_id
        for ldap_user_id in existing_user_ids:
            odoo_user_id = ResUsers.with_context(active_test=False).search(
                [('ldap_user_id', '=', ldap_user_id.id)],
                limit=1,
            )
            odoo_user_id.with_context(ldap_sync=True).sudo().write(
                self._prepare_odoo_user_values(ldap_user_id),
            )
        if self.deactivate_non_ldap_users:
            non_ldap_users = ResUsers.with_context(active_test=False).search(
                [('ldap_user_id', '=', False)],
            )
            users_to_deactivate = (
                non_ldap_users - self.ignore_non_ldap_user_ids - self.env.user
            )
            users_to_deactivate.sudo().write(
                self._prepare_nonldap_odoo_user_values(),
            )
            users_to_deactivate.sudo().unset_password()

    @api.multi
    def _sync_group_membership(self):
        self.ensure_one()
        ResUsers = self.env['res.users'].sudo()
        ldap_user_ids = ResUsers.with_context(active_test=False).search(
            [('ldap_user_id', '!=', False)],
        )
        for user_id in ldap_user_ids.with_context(ldap_sync=True).sudo():
            mapping_ids = user_id.ldap_user_id.ldap_group_ids.mapped(
                'mapping_ids'
            )
            user_id.groups_id = mapping_ids.mapped('odoo_group_ids')

    @api.multi
    def _sync_single_user(self, user_dn):
        self.ensure_one()
        # NOTE: do not sync groups, meaningless?
        # query single user
