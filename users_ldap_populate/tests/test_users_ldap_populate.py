# Copyright 2016-2018 Therp BV <https://therp.nl>.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from contextlib import contextmanager

from odoo.tests.common import TransactionCase


class PatchLDAPConnection:
    def __init__(self, results):
        self.results = results

    def simple_bind_s(self, user, password):
        return True

    def search_st(self, base, scope, ldap_filter, attributes, timeout=None):
        if ldap_filter == "(uid=*)":
            return self.results
        else:
            return []

    def unbind(self):
        return True


@contextmanager
def patch_ldap(self, results):
    """defuse ldap functions to return fake entries instead of talking to a
    server. Use this in your own ldap related tests"""
    import ldap

    original_initialize = ldap.initialize

    def initialize(uri):
        return PatchLDAPConnection(results)

    ldap.initialize = initialize
    yield
    ldap.initialize = original_initialize


def get_fake_ldap(self):
    company = self.env.ref("base.main_company")
    company.write(
        {
            "ldaps": [
                (
                    0,
                    0,
                    {
                        "ldap_server": "fake",
                        "ldap_server_port": 389,
                        "ldap_filter": "(uid=%s)",
                        "ldap_base": "fake",
                        "deactivate_unknown_users": True,
                        "no_deactivate_user_ids": [
                            (6, 0, [self.env.ref("base.user_admin").id])
                        ],
                    },
                )
            ],
        }
    )
    return company.ldaps.filtered(lambda x: x.ldap_server == "fake")


class TestUsersLdapPopulate(TransactionCase):
    def test_users_ldap_populate(self):
        previous_users_count = self.env["res.users"].search_count([])
        with patch_ldap(
            self,
            [
                (
                    "DN=fake",
                    {"cn": ["fake"], "uid": ["fake"], "mail": ["fake@fakery.com"]},
                )
            ],
        ):
            ldap = get_fake_ldap(self)
            res = ldap.populate_wizard()
            ldap_populate_wizard = self.env["res.company.ldap.populate_wizard"].browse(
                res["res_id"]
            )
            self.assertEqual(ldap_populate_wizard.users_created, 1)
            self.assertEqual(
                ldap_populate_wizard.users_deactivated, previous_users_count - 1
            )  # Admin is not deactivated
            self.assertFalse(self.env.ref("base.user_demo").active)
            self.assertTrue(self.env.ref("base.user_admin").active)
            self.assertTrue(self.env["res.users"].search([("login", "=", "fake")]))

    def test_users_ldap_populate_reactivate(self):
        # Create deactivated user
        inactive_user = self.env["res.users"].create(
            {"name": "test_inactive", "login": "test_inactive", "active": False}
        )
        with patch_ldap(
            self,
            [
                (
                    "DN=test_inactive",
                    {
                        "cn": ["test_inactive"],
                        "uid": ["test_inactive"],
                        "mail": ["test_inactive@fakery.com"],
                    },
                )
            ],
        ):
            ldap = get_fake_ldap(self)
            res = ldap.populate_wizard()
            ldap_populate_wizard = self.env["res.company.ldap.populate_wizard"].browse(
                res["res_id"]
            )
            self.assertEqual(ldap_populate_wizard.users_created, 1)
            self.assertTrue(inactive_user.active)
            self.assertTrue(
                self.env["res.users"].search([("login", "=", "test_inactive")])
            )
