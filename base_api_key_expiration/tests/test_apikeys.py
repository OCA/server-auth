# Copyright 2026 Camptocamp SA
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

import time
from datetime import timedelta

from psycopg2 import IntegrityError

from odoo import Command, fields
from odoo.exceptions import AccessDenied, ValidationError
from odoo.http import _request_stack
from odoo.tests import TransactionCase, new_test_user, tagged
from odoo.tools import SQL, DotDict, mute_logger

from odoo.addons.base.models.res_users import INDEX_SIZE


# post_install: the test on trusted devices needs auth_totp to be loaded
@tagged("post_install", "-at_install")
class TestApikeys(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = new_test_user(cls.env, "apikey_user", groups="base.group_user")
        cls.Apikeys = cls.env["res.users.apikeys"].with_user(cls.user)

    def _in_days(self, days):
        return fields.Datetime.now() + timedelta(days=days)

    def _generate(self, apikeys, name, expiration_date=None):
        return apikeys.with_context(api_key_expiration_date=expiration_date)._generate(
            None, name
        )

    def _expire(self, key):
        self.env.cr.execute(
            SQL(
                "UPDATE res_users_apikeys"
                " SET expiration_date = now() at time zone 'utc' - INTERVAL '1 hour'"
                " WHERE index = %s",
                key[:INDEX_SIZE],
            )
        )

    def _check_rpc(self, key):
        self.user.with_user(self.user)._check_credentials(key, {"interactive": False})

    def test_expiration_date_required(self):
        with self.assertRaisesRegex(ValidationError, "must have an expiration date"):
            self._generate(self.Apikeys, "no date")
        with self.assertRaisesRegex(ValidationError, "cannot exceed 90.0 days"):
            self._generate(self.Apikeys, "too long", self._in_days(91))
        self._generate(self.Apikeys, "ok", self._in_days(90))
        self.assertEqual(len(self.user.api_key_ids), 1)

    def test_expiration_date_stored(self):
        expiration_date = self._in_days(1)
        self._generate(self.Apikeys, "stored", expiration_date)
        self.assertEqual(self.user.api_key_ids.expiration_date, expiration_date)

    def test_trusted_device_without_expiration_date(self):
        """The 17.0 auth_totp controller creates devices without expiration date"""
        if "auth_totp.device" not in self.env:
            self.skipTest("auth_totp is not installed")
        self.env["auth_totp.device"].with_user(self.user)._generate(
            "browser", "Test browser"
        )
        self.assertEqual(
            self.env["auth_totp.device"].search_count([("user_id", "=", self.user.id)]),
            1,
        )

    def test_max_duration_from_groups(self):
        group = self.env["res.groups"].create(
            {
                "name": "Long keys",
                "api_key_duration": 365,
                "users": [Command.link(self.user.id)],
            }
        )
        self._generate(self.Apikeys, "one year", self._in_days(365))
        with mute_logger("odoo.sql_db"), self.assertRaises(IntegrityError):
            with self.env.cr.savepoint():
                group.api_key_duration = -1
                group.flush_recordset()

    def test_admin_persistent_key(self):
        admin = self.env.ref("base.user_admin")
        apikeys = self.env["res.users.apikeys"].with_user(admin)
        key = self._generate(apikeys, "persistent")
        self.assertEqual(apikeys._check_credentials(scope="rpc", key=key), admin.id)

    @mute_logger("odoo.addons.base.models.res_users")
    def test_expired_key_refused(self):
        key = self._generate(self.Apikeys, "rpc", self._in_days(1))
        self._check_rpc(key)
        self._expire(key)
        with self.assertRaises(AccessDenied):
            self._check_rpc(key)

    def test_gc_user_apikeys(self):
        expired_key = self._generate(self.Apikeys, "expired", self._in_days(1))
        self._expire(expired_key)
        self._generate(self.Apikeys, "valid", self._in_days(1))
        self._generate(self.Apikeys.sudo(), "persistent")
        self.env["res.users.apikeys"]._gc_user_apikeys()
        self.assertEqual(
            sorted(self.user.api_key_ids.mapped("name")), ["persistent", "valid"]
        )

    def test_wizard(self):
        description = self.env["res.users.apikeys.description"]
        self.assertIn("0", dict(description._selection_duration()))
        description = description.with_user(self.user)
        self.assertEqual(
            [value for value, __ in description._selection_duration()],
            ["1", "7", "30", "90", "-1"],
        )
        wizard = description.create({"name": "wizard", "duration": "7"})
        # bypass check_identity, like base/tests/test_xmlrpc.py
        _request_stack.push(
            DotDict(
                {
                    "httprequest": DotDict({"environ": {"REMOTE_ADDR": "localhost"}}),
                    "session": {"identity-check-last": time.time()},
                }
            )
        )
        self.addCleanup(_request_stack.pop)
        wizard.make_key()
        self.assertEqual(
            self.user.api_key_ids.expiration_date.date(),
            (fields.Datetime.now() + timedelta(days=7)).date(),
        )
        with self.assertRaises(ValidationError):
            description.create(
                {
                    "name": "custom",
                    "duration": "-1",
                    "expiration_date": self._in_days(91),
                }
            )

    def test_wizard_create_multi(self):
        descriptions = (
            self.env["res.users.apikeys.description"]
            .with_user(self.user)
            .create([{"name": "a", "duration": "1"}, {"name": "b", "duration": "7"}])
        )
        self.assertEqual(len(descriptions), 2)
