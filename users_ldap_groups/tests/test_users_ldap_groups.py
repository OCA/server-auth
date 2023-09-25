# Copyright 2018 Therp BV <https://therp.nl>
# Copyright 2018 Brainbean Apps <https://brainbeanapps.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from contextlib import contextmanager
from unittest import mock

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase

_auth_ldap_ns = "odoo.addons.auth_ldap"
_company_ldap_class = _auth_ldap_ns + ".models.res_company_ldap.CompanyLDAP"


@contextmanager
def mock_cursor(cr):
    with mock.patch("odoo.sql_db.Connection.cursor") as mocked_cursor_call:
        org_close = cr.close
        org_autocommit = cr.autocommit
        try:
            cr.close = mock.Mock()
            cr.autocommit = mock.Mock()
            cr.commit = mock.Mock()
            mocked_cursor_call.return_value = cr
            yield
        finally:
            cr.close = org_close
    cr.autocommit = org_autocommit


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
        self.group_system = self.env.ref("base.group_system")
        self.group_user = self.env.ref("base.group_user")
        self.group_contains = self.env["res.groups"].create({"name": "contains"})
        self.group_equals = self.env["res.groups"].create({"name": "equals"})
        self.group_query = self.env["res.groups"].create({"name": "query"})

    def _create_ldap_config(self, groups, only_ldap_groups=False, cr=None):
        vals = {
            "company": self.env.ref("base.main_company").id,
            "ldap_base": "dc=users_ldap_groups,dc=example,dc=com",
            "ldap_filter": "(uid=%s)",
            "ldap_binddn": "cn=bind,dc=example,dc=com",
            "create_user": True,
            "only_ldap_groups": only_ldap_groups,
            "group_mapping_ids": [(0, 0, group) for group in groups],
        }
        return self.env["res.company.ldap"].create(vals)

    def test_users_ldap_groups_only_true(self):
        self._create_ldap_config(
            groups=[
                {
                    "ldap_attribute": "name",
                    "operator": "contains",
                    "value": "hello3",
                    "group_id": self.group_system.id,
                },
                {
                    "ldap_attribute": "name",
                    "operator": "contains",
                    "value": "hello",
                    "group_id": self.group_user.id,
                },
                {
                    "ldap_attribute": "name",
                    "operator": "contains",
                    "value": "hello2",
                    "group_id": self.group_contains.id,
                },
                {
                    "ldap_attribute": "name",
                    "operator": "equals",
                    "value": "hello",
                    "group_id": self.group_equals.id,
                },
                {
                    "ldap_attribute": "",
                    "operator": "query",
                    "value": "is not run because of patching",
                    "group_id": self.group_query.id,
                },
            ],
            only_ldap_groups=True,
        )
        # _login does its work in a new cursor, so we need to mock it
        with mock.patch(
            _company_ldap_class + "._connect",
            return_value=FakeLdapConnection(
                {
                    "dc=users_ldap_groups,dc=example,dc=com": {
                        "cn": [b"User Name"],
                        "name": [b"hello", b"hello2"],
                    }
                }
            ),
        ), mock_cursor(self.cr):
            user_id = (
                self.env["res.users"]
                .sudo()
                .authenticate(
                    self.env.cr.dbname, "users_ldap_groups-username", "password", {}
                )
            )
        # this asserts group mappings from demo data
        user = self.env["res.users"].sudo().browse(user_id)
        groups = user.groups_id
        self.assertIn(self.group_contains, groups)
        self.assertIn(self.group_user, groups)
        self.assertNotIn(self.group_equals, groups)
        self.assertIn(self.group_query, groups)
        self.assertNotIn(self.group_system, groups)

    def test_users_ldap_groups_only_false(self):
        self._create_ldap_config(
            groups=[
                {
                    "ldap_attribute": "name",
                    "operator": "contains",
                    "value": "hello2",
                    "group_id": self.group_contains.id,
                },
                {
                    "ldap_attribute": "name",
                    "operator": "contains",
                    "value": "hello",
                    "group_id": self.group_equals.id,
                },
            ],
            only_ldap_groups=False,
        )
        with mock.patch(
            _company_ldap_class + "._connect",
            return_value=FakeLdapConnection(
                {
                    "dc=users_ldap_groups,dc=example,dc=com": {
                        "cn": [b"User Name"],
                        "name": [b"hello", b"hello2"],
                    }
                }
            ),
        ), mock_cursor(self.cr):
            user_id = (
                self.env["res.users"]
                .sudo()
                .authenticate(
                    self.env.cr.dbname, "users_ldap_groups-username", "password", {}
                )
            )
        # this asserts group mappings from demo data
        user = self.env["res.users"].sudo().browse(user_id)
        groups = user.groups_id
        self.assertIn(self.group_contains, groups)
        self.assertIn(self.group_equals, groups)
        self.assertGreater(len(groups), 2)  # user should keep default groups

    def _test_users_ldap_groups_not_user_type(self):
        self._create_ldap_config(
            groups=[
                {
                    "ldap_attribute": "name",
                    "operator": "contains",
                    "value": "hello3",
                    "group_id": self.group_system.id,
                },
                {
                    "ldap_attribute": "name",
                    "operator": "contains",
                    "value": "hello2",
                    "group_id": self.group_contains.id,
                },
                {
                    "ldap_attribute": "name",
                    "operator": "equals",
                    "value": "hello",
                    "group_id": self.group_equals.id,
                },
                {
                    "ldap_attribute": "",
                    "operator": "query",
                    "value": "is not run because of patching",
                    "group_id": self.group_query.id,
                },
            ],
            only_ldap_groups=True,
        )
        with mock.patch(
            _company_ldap_class + "._connect",
            return_value=FakeLdapConnection(
                {
                    "dc=users_ldap_groups,dc=example,dc=com": {
                        "cn": [b"User Name"],
                        "name": [b"hello", b"hello2"],
                    }
                }
            ),
        ), mock_cursor(self.cr):
            with self.assertRaises(UserError):
                self.env["res.users"].sudo().authenticate(
                    self.env.cr.dbname, "users_ldap_groups-username", "password", {}
                )
