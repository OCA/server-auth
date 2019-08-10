# Copyright 2019 Brainbean Apps (https://brainbeanapps.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from copy import deepcopy
import ldap
import logging
from unittest import mock

from odoo.tests import common
from odoo.tools.misc import mute_logger

_logger = logging.getLogger(__name__)

_ldap_sync_ns = 'odoo.addons.ldap_sync'
_auth_ldap_ns = 'odoo.addons.auth_ldap'
_company_ldap_class = _auth_ldap_ns + '.models.res_company_ldap.CompanyLDAP'


class FakeLdapConnection(object):
    def __init__(self, entries):
        self.entries = deepcopy(entries)

    def simple_bind_s(self, dn, passwd):
        pass

    def search_st(self, dn, scope, ldap_filter, attributes, timeout):
        if dn in self.entries:
            return deepcopy(self.entries[dn])
        return None

    def unbind(self):
        pass

    def unbind_s(self):
        pass

    def __getattr__(self, name):
        def wrapper():
            raise Exception("'%s' is not mocked" % name)
        return wrapper


class TestLdapSync(common.TransactionCase):

    def setUp(self):
        super().setUp()

        self.ResUsers = self.env['res.users']
        self.ResGroups = self.env['res.groups']
        self.ResCompanyLdap = self.env['res.company.ldap']
        self.group_system = self.env.ref('base.group_system')
        self.company_id = self.env['res.company']._company_default_get()
        self.groups_base_dn = 'cn=groups,dc=example,dc=com'
        self.users_base_dn = 'cn=users,dc=example,dc=com'
        self.mocked_group_1 = (
            ('cn=group1,' + self.groups_base_dn), {
                'cn': [b'group1'],
            }
        )
        self.mocked_group_2 = (
            ('cn=group2,' + self.groups_base_dn), {
                'cn': [b'group2'],
            }
        )
        self.mocked_user_1 = (
            ('cn=user1,' + self.users_base_dn), {
                'uid': [b'user1'],
                'cn': [b'User 1'],
                'mail': [b'user1@example.com'],
                'objectGUID': [b'1'],
                'memberOf': [
                    b'cn=group1,cn=groups,dc=example,dc=com',
                ],
            }
        )
        self.mocked_user_2 = (
            ('cn=user2,' + self.users_base_dn), {
                'uid': [b'user2'],
                'cn': [b'User 2'],
                'mail': [b'user2@example.com'],
                'objectGUID': [b'2'],
                'memberOf': [],
            }
        )
        self.mocked_user_3 = (
            ('cn=user3,' + self.users_base_dn), {
                'uid': [b'user3'],
                'cn': [b'User 3'],
                'mail': [b'user3@example.com'],
                'objectGUID': [b'3'],
                'memberOf': [],
            }
        )

    def test_sync_groups(self):
        company_ldap = self.ResCompanyLdap.sudo().create({
            'company': self.company_id.id,
            'ldap_base': 'cn=users,dc=example,dc=com',
            'ldap_filter': '(uid=%s)',
            'ldap_binddn': 'cn=bind,dc=example,dc=com',
            'create_user': True,
            'groups_base_dn': self.groups_base_dn,
            'users_base_dn': self.users_base_dn,
        })

        with mock.patch(
            _company_ldap_class + '._connect',
            return_value=FakeLdapConnection({
                self.groups_base_dn: [
                    self.mocked_group_1,
                ],
                self.users_base_dn: [],
            }),
        ):
            company_ldap._sync()
        self.assertEquals(len(company_ldap.ldap_group_ids), 1)
        self.assertEquals(
            company_ldap.ldap_group_ids[0].dn,
            'cn=group1,cn=groups,dc=example,dc=com'
        )

        company_ldap.ldap_group_mapping_ids = [(0, 0, {
            'ldap_group_id': company_ldap.ldap_group_ids[0].id,
            'odoo_group_ids': [(4, self.group_system.id, 0)],
        })]

        with mock.patch(
            _company_ldap_class + '._connect',
            return_value=FakeLdapConnection({
                self.groups_base_dn: [
                    self.mocked_group_1,
                ],
                self.users_base_dn: [],
            }),
        ):
            company_ldap._sync()
        self.assertEquals(len(company_ldap.ldap_group_ids), 1)
        self.assertEquals(
            company_ldap.ldap_group_ids[0].dn,
            'cn=group1,cn=groups,dc=example,dc=com'
        )
        self.assertEquals(len(company_ldap.ldap_group_mapping_ids), 1)
        self.assertEquals(len(company_ldap.ldap_group_ids[0].mapping_ids), 1)

        with mock.patch(
            _company_ldap_class + '._connect',
            return_value=FakeLdapConnection({
                self.groups_base_dn: [
                    self.mocked_group_2,
                ],
                self.users_base_dn: [],
            }),
        ):
            company_ldap._sync()
        self.assertEquals(len(company_ldap.ldap_group_ids), 1)
        self.assertEquals(
            company_ldap.ldap_group_ids[0].dn,
            'cn=group2,cn=groups,dc=example,dc=com'
        )
        self.assertEquals(len(company_ldap.ldap_group_mapping_ids), 1)

    def test_users_sync(self):
        company_ldap = self.ResCompanyLdap.sudo().create({
            'company': self.company_id.id,
            'ldap_base': 'cn=users,dc=example,dc=com',
            'ldap_filter': '(uid=%s)',
            'ldap_binddn': 'cn=bind,dc=example,dc=com',
            'create_user': True,
            'groups_base_dn': self.groups_base_dn,
            'users_base_dn': self.users_base_dn,
        })

        user_3 = self.ResUsers.sudo().create({
            'name': 'Not User 3',
            'login': 'user3',
            'email': 'not.user.3@example.com',
            'company_id': self.company_id.id,
            'active': False,
        })

        with mock.patch(
            _company_ldap_class + '._connect',
            return_value=FakeLdapConnection({
                self.groups_base_dn: [],
                self.users_base_dn: [
                    self.mocked_user_1,
                    self.mocked_user_2,
                    self.mocked_user_3,
                ],
            }),
        ):
            company_ldap._sync()
        user_1 = self.ResUsers.search([
            ('login', '=', 'user1'),
            ('active', '=', True),
        ])
        self.assertTrue(user_1)
        self.assertTrue(user_1.ldap_user_id)
        user_2 = self.ResUsers.search([
            ('login', '=', 'user2'),
            ('active', '=', True),
        ])
        self.assertTrue(user_2)
        self.assertTrue(user_2.ldap_user_id)

        self.assertTrue(user_3.active)
        self.assertEquals(user_3.name, 'User 3')
        self.assertEquals(user_3.email, 'user3@example.com')

        with mock.patch(
            _company_ldap_class + '._connect',
            return_value=FakeLdapConnection({
                self.groups_base_dn: [],
                self.users_base_dn: [
                    self.mocked_user_1,
                ],
            }),
        ):
            company_ldap._sync()
        user_1 = self.ResUsers.search([
            ('login', '=', 'user1'),
            ('active', '=', True),
        ])
        self.assertTrue(user_1)
        self.assertTrue(user_1.ldap_user_id)
        user_2 = self.ResUsers.search([
            ('login', '=', 'user2'),
            ('active', '=', False),
        ])
        self.assertTrue(user_2)
        self.assertFalse(user_2.ldap_user_id)

        ignored_user = self.ResUsers.sudo().create({
            'name': 'Ignored User',
            'login': 'ignored_user',
            'email': 'ignored.user@example.com',
            'company_id': self.company_id.id,
        })
        non_ignored_user = self.ResUsers.sudo().create({
            'name': 'Non-Ignored User',
            'login': 'non_ignored_user',
            'email': 'non.ignored.user@example.com',
            'company_id': self.company_id.id,
        })
        self.assertTrue(ignored_user.active)
        self.assertTrue(non_ignored_user.active)
        company_ldap.ignore_non_ldap_user_ids |= ignored_user
        company_ldap.deactivate_non_ldap_users = True
        with mock.patch(
            _company_ldap_class + '._connect',
            return_value=FakeLdapConnection({
                self.groups_base_dn: [],
                self.users_base_dn: [],
            }),
        ):
            company_ldap._sync()
        self.assertTrue(ignored_user.active)
        self.assertFalse(non_ignored_user.active)

    def test_group_membership_sync(self):
        company_ldap = self.ResCompanyLdap.sudo().create({
            'company': self.company_id.id,
            'ldap_base': 'cn=users,dc=example,dc=com',
            'ldap_filter': '(uid=%s)',
            'ldap_binddn': 'cn=bind,dc=example,dc=com',
            'create_user': True,
            'groups_base_dn': self.groups_base_dn,
            'users_base_dn': self.users_base_dn,
            'sync_group_membership': True,
        })

        with mock.patch(
            _company_ldap_class + '._connect',
            return_value=FakeLdapConnection({
                self.groups_base_dn: [
                    self.mocked_group_1,
                    self.mocked_group_2,
                ],
                self.users_base_dn: [
                    self.mocked_user_1,
                    self.mocked_user_2,
                ],
            }),
        ):
            company_ldap._sync()

        user_1 = self.ResUsers.search([('login', '=', 'user1')], limit=1)
        user_2 = self.ResUsers.search([('login', '=', 'user2')], limit=1)

        ldap_group_1 = company_ldap.ldap_group_ids.filtered(
            lambda x: x.dn == 'cn=group1,cn=groups,dc=example,dc=com'
        )
        group_1 = self.ResGroups.sudo().create({
            'name': 'Group 1',
        })
        ldap_group_2 = company_ldap.ldap_group_ids.filtered(
            lambda x: x.dn == 'cn=group2,cn=groups,dc=example,dc=com'
        )
        group_2 = self.ResGroups.sudo().create({
            'name': 'Group 1',
        })
        company_ldap.ldap_group_mapping_ids = [
            (0, 0, {
                'ldap_group_id': ldap_group_1.id,
                'odoo_group_ids': [
                    (4, group_1.id, 0),
                ],
            }),
            (0, 0, {
                'ldap_group_id': ldap_group_2.id,
                'odoo_group_ids': [
                    (4, group_2.id, 0),
                ],
            }),
        ]
        self.assertEquals(len(ldap_group_1.mapping_ids), 1)
        self.assertEquals(len(ldap_group_2.mapping_ids), 1)

        with mock.patch(
            _company_ldap_class + '._connect',
            return_value=FakeLdapConnection({
                self.groups_base_dn: [
                    self.mocked_group_1,
                    self.mocked_group_2,
                ],
                self.users_base_dn: [
                    self.mocked_user_1,
                    self.mocked_user_2,
                ],
            }),
        ):
            company_ldap._sync()

        self.assertEquals(len(ldap_group_1.mapping_ids), 1)
        self.assertEquals(len(ldap_group_2.mapping_ids), 1)
        self.assertIn(group_1, user_1.groups_id)
        self.assertNotIn(group_2, user_1.groups_id)
        self.assertFalse(user_2.groups_id)

        with mock.patch(
            _company_ldap_class + '._connect',
            return_value=FakeLdapConnection({
                self.groups_base_dn: [],
                self.users_base_dn: [
                    self.mocked_user_1,
                    self.mocked_user_2,
                ],
            }),
        ):
            company_ldap._sync()

        self.assertNotIn(group_1, user_1.groups_id)
        self.assertNotIn(group_2, user_1.groups_id)
        self.assertFalse(user_2.groups_id)

    def test_scheduled_sync(self):
        company_ldap = self.ResCompanyLdap.sudo().create({
            'company': self.company_id.id,
            'ldap_base': 'cn=users,dc=example,dc=com',
            'ldap_filter': '(uid=%s)',
            'ldap_binddn': 'cn=bind,dc=example,dc=com',
            'create_user': True,
            'groups_base_dn': self.groups_base_dn,
            'users_base_dn': self.users_base_dn,
        })

        with mock.patch(
            _company_ldap_class + '._connect',
            return_value=FakeLdapConnection({
                self.groups_base_dn: [],
                self.users_base_dn: [
                    self.mocked_user_1,
                    self.mocked_user_2,
                    self.mocked_user_3,
                ],
            }),
        ):
            self.ResCompanyLdap._scheduled_sync()
            company_ldap._scheduled_sync()

    def test_query_failed(self):
        company_ldap = self.ResCompanyLdap.sudo().create({
            'company': self.company_id.id,
            'ldap_base': 'cn=users,dc=example,dc=com',
            'ldap_filter': '(uid=%s)',
            'ldap_binddn': 'cn=bind,dc=example,dc=com',
            'create_user': True,
            'groups_base_dn': self.groups_base_dn,
            'users_base_dn': self.users_base_dn,
        })

        with mock.patch(
            _company_ldap_class + '._connect',
            return_value=FakeLdapConnection({
                self.groups_base_dn: [
                    self.mocked_group_1,
                ],
                self.users_base_dn: [],
            }),
        ):
            company_ldap._sync()
        self.assertEquals(len(company_ldap.ldap_group_ids), 1)
        self.assertEquals(
            company_ldap.ldap_group_ids[0].dn,
            'cn=group1,cn=groups,dc=example,dc=com'
        )

        company_ldap.ldap_group_mapping_ids = [(0, 0, {
            'ldap_group_id': company_ldap.ldap_group_ids[0].id,
            'odoo_group_ids': [(4, self.group_system.id, 0)],
        })]

        with mock.patch(
            _company_ldap_class + '._connect',
            return_value=FakeLdapConnection({
                self.groups_base_dn: [
                    self.mocked_group_1,
                ],
                self.users_base_dn: [],
            }),
        ):
            company_ldap._sync()
        self.assertEquals(len(company_ldap.ldap_group_ids), 1)
        self.assertEquals(
            company_ldap.ldap_group_ids[0].dn,
            'cn=group1,cn=groups,dc=example,dc=com'
        )
        self.assertEquals(len(company_ldap.ldap_group_mapping_ids), 1)
        self.assertEquals(len(company_ldap.ldap_group_ids[0].mapping_ids), 1)

        with mock.patch(
            _company_ldap_class + '._connect',
            side_effect=ldap.LDAPError(),
        ), mute_logger(_ldap_sync_ns + '.models.res_company_ldap'):
            company_ldap._sync()
        self.assertEquals(len(company_ldap.ldap_group_ids), 1)
        self.assertEquals(
            company_ldap.ldap_group_ids[0].dn,
            'cn=group1,cn=groups,dc=example,dc=com'
        )
        self.assertEquals(len(company_ldap.ldap_group_mapping_ids), 1)
        self.assertEquals(len(company_ldap.ldap_group_ids[0].mapping_ids), 1)
