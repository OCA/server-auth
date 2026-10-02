# Copyright 2026 spomata
# License: AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

import json

from odoo.tests.common import TransactionCase, new_test_user

LOGGER = "odoo.addons.auth_oauth_link_by_email.models.res_users"


class TestAuthOAuthLinkByEmail(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.provider = cls.env["auth.oauth.provider"].create(
            {
                "name": "OAuth Provider for TestAuthOAuthLinkByEmail",
                "client_id": "auth_oauth_link_by_email-test",
                "enabled": True,
                "body": "Config of an oauth provider for tests",
                "auth_endpoint": "https://idp.example.test/authorize",
                "validation_endpoint": "https://idp.example.test/userinfo",
                "link_user_by_verified_email": True,
            }
        )
        cls.user = new_test_user(cls.env, login="alice_doe@example.test")
        cls.Users = cls.env["res.users"].with_context(no_user_creation=True)

    def _signin(self, **claims):
        validation = {
            "user_id": "subject-alice",
            "email": "alice_doe@example.test",
            "email_verified": True,
            **claims,
        }
        params = {"access_token": "42", "state": json.dumps({})}
        return self.Users._auth_oauth_signin(self.provider.id, validation, params)

    def _assert_not_linked(self, user=None, **claims):
        user = user or self.user
        self.assertIsNone(self._signin(**claims))
        self.assertFalse(user.oauth_uid)

    def test_link_by_login(self):
        self.assertEqual(self._signin(), "alice_doe@example.test")
        self.assertEqual(self.user.oauth_provider_id, self.provider)
        self.assertEqual(self.user.oauth_uid, "subject-alice")
        # the next login is resolved by subject, whatever the email
        self.assertEqual(
            self._signin(email="changed@example.test"), "alice_doe@example.test"
        )

    def test_link_case_insensitive(self):
        self.assertEqual(
            self._signin(email="Alice_Doe@Example.test"), "alice_doe@example.test"
        )
        self.assertEqual(self.user.oauth_uid, "subject-alice")

    def test_email_field_not_matched(self):
        user = new_test_user(self.env, login="bob", email="bob@example.test")
        self._assert_not_linked(user=user, email="bob@example.test")

    def test_option_disabled(self):
        self.provider.link_user_by_verified_email = False
        self._assert_not_linked()

    def test_email_not_verified(self):
        with self.assertLogs(LOGGER, "INFO") as logs:
            self._assert_not_linked(email_verified=False)
        self.assertIn("is not verified", logs.output[0])
        self._assert_not_linked(email_verified="true")
        self._assert_not_linked(email_verified=None)

    def test_no_email(self):
        with self.assertLogs(LOGGER, "INFO") as logs:
            self._assert_not_linked(email=None)
        self.assertIn("no email claim", logs.output[0])

    def test_no_matching_user(self):
        with self.assertLogs(LOGGER, "INFO") as logs:
            self._assert_not_linked(email="nobody@example.test")
        self.assertIn("no active user has nobody@example.test as login", logs.output[0])

    def test_linked_user_login_is_silent(self):
        self._signin()
        with self.assertNoLogs(LOGGER, "INFO"):
            self.assertEqual(self._signin(), "alice_doe@example.test")

    def test_email_is_not_a_pattern(self):
        self._assert_not_linked(email="alice%@example.test")
        self._assert_not_linked(email="alice_doe@example_test")
        self._assert_not_linked(email="alicexdoe@example.test")

    def test_ambiguous_login(self):
        other = new_test_user(self.env, login="alice2@example.test")
        # in SQL, as auth_user_case_insensitive lowercases logins in the ORM:
        # such duplicates exist when they predate it
        self.env.cr.execute(
            "UPDATE res_users SET login = %s WHERE id = %s",
            ("Alice_Doe@example.test", other.id),
        )
        other.invalidate_recordset(["login"])
        with self.assertLogs(LOGGER, "WARNING") as logs:
            self._assert_not_linked()
        self.assertIn("2 users have its email as login", logs.output[0])
        self.assertFalse(other.oauth_uid)

    def test_already_linked_user(self):
        self.user.write(
            {"oauth_provider_id": self.provider.id, "oauth_uid": "subject-other"}
        )
        with self.assertLogs(LOGGER, "WARNING") as logs:
            self.assertIsNone(self._signin())
        self.assertIn("already linked to another subject", logs.output[0])
        self.assertEqual(self.user.oauth_uid, "subject-other")

    def test_administrator(self):
        self.user.group_ids += self.env.ref("base.group_system")
        with self.assertLogs(LOGGER, "WARNING") as logs:
            self._assert_not_linked()
        self.assertIn("administrators must be linked manually", logs.output[0])

    def test_archived_user(self):
        self.user.active = False
        self._assert_not_linked()
