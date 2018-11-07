# Copyright 2018 Brainbean Apps
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import logging
from unittest import mock
from odoo.tests import common
from odoo import api, registry, SUPERUSER_ID

_logger = logging.getLogger(__name__)
_auth_ldap_ns = 'odoo.addons.auth_ldap'
_company_ldap_class = _auth_ldap_ns + '.models.res_company_ldap.CompanyLDAP'


class FakeLdapConnection(object):
    def __init__(self, entries):
        self.entries = entries

    def simple_bind_s(self, dn, passwd):
        pass

    def search_st(self, dn, scope, ldap_filter, attributes, timeout):
        if dn in self.entries:
            return [(dn, dict(self.entries[dn]))]
        return None

    def unbind(self):
        pass

    def unbind_s(self):
        pass

    def __getattr__(self, name):
        def wrapper():
            raise Exception("'%s' is not mocked" % name)
        return wrapper


class TestAuthLdapGroupSync(common.TransactionCase):

    def setUp(self):
        super().setUp()

        self.group_system = self.env.ref('base.group_system')

    def test_auth_ldap_group_sync(self):
        group1 = None
        group2 = None
        group3 = None
        with registry(self.env.cr.dbname).cursor() as cr:
            env = api.Environment(cr, SUPERUSER_ID, {})

            group1 = env['res.groups'].create({'name': 'group1'})
            group2 = env['res.groups'].create({'name': 'group2'})
            group3 = env['res.groups'].create({'name': 'group3'})

            company_ldap = env['res.company.ldap'].sudo().create({
                'company': env['res.company']._company_default_get().id,
                'ldap_base': 'dc=auth_ldap_group_sync,dc=example,dc=com',
                'ldap_filter': '(uid=%s)',
                'ldap_binddn': 'cn=bind,dc=example,dc=com',
                'create_user': True,
                'sync_ldap_group_membership_periodically': True,
                'ldap_group_membership_attribute': 'memberOf',
                'only_ldap_group_membership': True,
                'ldap_group_mapping_ids': [
                    (0, 0, {
                        'regexp': '^group\\d+$',
                        'group_ids': [
                            (4, self.group_system.id, False)
                        ],
                    }),
                    (0, 0, {
                        'regexp': '^group1$',
                        'group_ids': [
                            (4, group1.id, False)
                        ],
                    }),
                    (0, 0, {
                        'regexp': '^group2$',
                        'group_ids': [
                            (4, group2.id, False)
                        ],
                    }),
                    (0, 0, {
                        'regexp': '^group3$',
                        'group_ids': [
                            (4, group3.id, False)
                        ],
                    }),
                ],
            })

        with registry(self.env.cr.dbname).cursor() as cr:
            env = api.Environment(cr, SUPERUSER_ID, {})

            company = env['res.company'].sudo()._company_default_get()
            company.write({
                'ldaps': [(6, 0, [company_ldap.id])]
            })

        user_id = False
        with registry(self.env.cr.dbname).cursor() as cr:
            env = api.Environment(cr, SUPERUSER_ID, {})
            SudoUser = env['res.users'].sudo()
            with mock.patch(
                _company_ldap_class + '._connect',
                return_value=FakeLdapConnection({
                    'dc=auth_ldap_group_sync,dc=example,dc=com': {
                        'uid': [b'auth_ldap_group_sync-username'],
                        'cn': [b'User Name'],
                        'memberOf': [b'group1', b'group3']
                    }
                })
            ):
                user_id = SudoUser.authenticate(
                    env.cr.dbname,
                    'auth_ldap_group_sync-username',
                    'password',
                    {}
                )

        with registry(self.env.cr.dbname).cursor() as cr:
            env = api.Environment(cr, SUPERUSER_ID, {})
            SudoUser = env['res.users'].sudo()

            user = SudoUser.browse(user_id)
            groups = user.groups_id
            self.assertIn(group1, groups)
            self.assertNotIn(group2, groups)
            self.assertIn(group3, groups)
            self.assertIn(self.group_system, groups)

        with registry(self.env.cr.dbname).cursor() as cr:
            env = api.Environment(cr, SUPERUSER_ID, {})
            SudoUser = env['res.users'].sudo()
            with mock.patch(
                _company_ldap_class + '._connect',
                return_value=FakeLdapConnection({
                    'dc=auth_ldap_group_sync,dc=example,dc=com': {
                        'uid': [b'auth_ldap_group_sync-username'],
                        'cn': [b'User Name'],
                        'memberOf': [b'group2']
                    }
                })
            ):
                env['res.company.ldap'].sudo()._sync_group_membership()

        with registry(self.env.cr.dbname).cursor() as cr:
            env = api.Environment(cr, SUPERUSER_ID, {})
            SudoUser = env['res.users'].sudo()

            user = SudoUser.browse(user_id)
            groups = user.groups_id
            self.assertNotIn(group1, groups)
            self.assertIn(group2, groups)
            self.assertNotIn(group3, groups)
            self.assertIn(self.group_system, groups)
