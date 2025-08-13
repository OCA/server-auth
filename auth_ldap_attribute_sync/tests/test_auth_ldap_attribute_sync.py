# Copyright (C) 2018 Brainbean Apps
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import logging
from unittest.mock import patch

from odoo import SUPERUSER_ID, api
from odoo.modules.registry import Registry
from odoo.tests.common import HttpCase

_logger = logging.getLogger(__name__)
_auth_ldap_ns = "odoo.addons.auth_ldap"
_company_ldap_class = _auth_ldap_ns + ".models.res_company_ldap.CompanyLDAP"


class FakeLdapConnection:
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
            raise Exception(f"'{name}' is not mocked")

        return wrapper


class TestAuthLdapAttributeSync(HttpCase):
    def test_auth_ldap_attribute_sync(self):
        with Registry(self.env.cr.dbname).cursor() as cr:
            env = api.Environment(cr, SUPERUSER_ID, {})

            env["res.company.ldap"].sudo().create(
                {
                    "company": self.env.company.id,
                    "ldap_base": "dc=example,dc=com",
                    "ldap_filter": "(uid=%s)",
                    "ldap_binddn": "cn=bind,dc=example,dc=com",
                    "create_user": True,
                    "user_attributes_mapping": [
                        (
                            0,
                            0,
                            {
                                "attribute_name": "displayName",
                                "field_name": "name",
                                "mode": "initial",
                            },
                        ),
                        (
                            0,
                            0,
                            {
                                "attribute_name": "mail",
                                "field_name": "email",
                                "mode": "always",
                            },
                        ),
                    ],
                }
            )

        with Registry(self.env.cr.dbname).cursor() as cr:
            env = api.Environment(cr, SUPERUSER_ID, {})
            SudoUser = env["res.users"].sudo()

            with patch.object(
                self.registry["res.company.ldap"],
                "_connect",
                return_value=FakeLdapConnection(
                    {
                        "dc=example,dc=com": {
                            "cn": [b"User Name"],
                            "displayName": [b"User Name"],
                            "mail": [b"user@example.com"],
                        }
                    }
                ),
            ):
                self.authenticate(user="username", password="password")
            user = SudoUser.browse(self.session.uid)
            self.assertEqual(user.login, "username")
            self.assertEqual(user.name, "User Name")
            self.assertEqual(user.email, "user@example.com")

        with Registry(self.env.cr.dbname).cursor() as cr:
            env = api.Environment(cr, SUPERUSER_ID, {})
            SudoUser = env["res.users"].sudo()

            with patch.object(
                self.registry["res.company.ldap"],
                "_connect",
                return_value=FakeLdapConnection(
                    {
                        "dc=example,dc=com": {
                            "cn": [b"Altered User Name"],
                            "displayName": [b"Altered User Name"],
                            "mail": [b"altered.user@example.com"],
                        }
                    }
                ),
            ):
                self.authenticate(user="username", password="password")
            user = SudoUser.browse(self.session.uid)
            self.assertEqual(user.login, "username")
            self.assertEqual(user.name, "User Name")
            self.assertEqual(user.email, "altered.user@example.com")
