# Copyright 2018 Therp BV <https://therp.nl>
# Copyright 2018 Brainbean Apps <https://brainbeanapps.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from unittest import mock
from odoo.tests.common import TransactionCase
from odoo import api, registry, SUPERUSER_ID

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
        return []

    def unbind(self):
        pass

    def unbind_s(self):
        pass

    def __getattr__(self, name):
        def wrapper():
            raise Exception("'%s' is not mocked" % name)
        return wrapper


class TestUsersLdapGroups(TransactionCase):

    def setUp(self):
        super().setUp()

        self.group_system = self.env.ref('base.group_system')

    def test_users_ldap_groups(self):
        # _login does its work in a new cursor, so we need one too
        with registry(self.env.cr.dbname).cursor() as cr:
            env = api.Environment(cr, SUPERUSER_ID, {})

            group_contains = env['res.groups'].create({'name': 'contains'})
            group_equals = env['res.groups'].create({'name': 'equals'})
            group_query = env['res.groups'].create({'name': 'query'})
            env.ref('base.main_company').write({'ldaps': [
                (5, False, False),
                (0, 0, {
                    'ldap_base': 'dc=users_ldap_groups,dc=example,dc=com',
                    'ldap_filter': '(uid=%s)',
                    'ldap_binddn': 'cn=bind,dc=example,dc=com',
                    'create_user': True,
                    'only_ldap_groups': True,
                    'group_mapping_ids': [
                        (0, 0, {
                            'ldap_attribute': 'name',
                            'operator': 'contains',
                            'value': 'hello3',
                            'group_id': self.group_system.id,
                        }),
                        (0, 0, {
                            'ldap_attribute': 'name',
                            'operator': 'contains',
                            'value': 'hello2',
                            'group_id': group_contains.id,
                        }),
                        (0, 0, {
                            'ldap_attribute': 'name',
                            'operator': 'equals',
                            'value': 'hello',
                            'group_id': group_equals.id,
                        }),
                        (0, 0, {
                            'ldap_attribute': '',
                            'operator': 'query',
                            'value': 'is not run because of patching',
                            'group_id': group_query.id,
                        }),
                    ],
                })
            ]})

        with mock.patch(
                _company_ldap_class + '._connect',
                return_value=FakeLdapConnection({
                    'dc=users_ldap_groups,dc=example,dc=com': {
                        'cn': [b'User Name'],
                        'name': [b'hello', b'hello2']
                    }
                })
        ):
            user_id = self.env['res.users'].sudo().authenticate(
                self.env.cr.dbname,
                'users_ldap_groups-username',
                'password',
                {}
            )

        with registry(self.env.cr.dbname).cursor() as cr:
            env = api.Environment(cr, SUPERUSER_ID, {})

            # this asserts group mappings from demo data
            user = env['res.users'].sudo().browse(user_id)
            groups = user.groups_id
            self.assertIn(group_contains, groups)
            self.assertNotIn(group_equals, groups)
            self.assertIn(group_query, groups)
            self.assertNotIn(self.group_system, groups)
            # clean up
            env.ref('base.main_company').write({'ldaps': [(6, False, [])]})
