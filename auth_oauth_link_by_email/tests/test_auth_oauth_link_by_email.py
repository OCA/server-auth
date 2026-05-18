# Copyright 2026 Heligrafics <https://www.heligrafics.net>
# License: AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo.exceptions import AccessDenied
from odoo.tests import common
from odoo.tools import mute_logger


class TestOAuthLinkByEmail(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._provider_id = (
            cls.env["auth.oauth.provider"]
            .create(
                {
                    "name": "Test OAuth Provider",
                    "client_id": "test-client",
                    "body": "Log in with Test OAuth",
                    "auth_endpoint": "http://example.com/auth",
                    "validation_endpoint": "http://example.com/userinfo",
                    "scope": "openid email",
                    "enabled": True,
                }
            )
            .id
        )
        cls._test_user_id = (
            cls.env["res.users"]
            .create(
                {
                    "name": "OAuth Test User",
                    "login": "oauth.test@example.com",
                    "email": "oauth.test@example.com",
                    "groups_id": [(6, 0, [cls.env.ref("base.group_user").id])],
                }
            )
            .id
        )

    def setUp(self):
        super().setUp()
        self.provider = self.env["auth.oauth.provider"].browse(
            self.__class__._provider_id
        )
        self.test_user = self.env["res.users"].browse(self.__class__._test_user_id)

    def _make_validation(self, user_id="sub-uuid-1234", email="oauth.test@example.com"):
        return {"user_id": user_id, "email": email}

    def _make_params(self, access_token="test_token"):
        return {"access_token": access_token, "state": "{}"}

    def test_link_user_by_email_links_and_returns_user(self):
        """Links the user found by email and returns the recordset."""
        oauth_uid = "sub-uuid-9999"
        result = self.env["res.users"]._oauth_link_user_by_email(
            self.provider.id, oauth_uid, "oauth.test@example.com", "token-abc"
        )
        self.assertEqual(result, self.test_user)
        self.assertEqual(self.test_user.oauth_uid, oauth_uid)
        self.assertEqual(self.test_user.oauth_provider_id, self.provider)
        self.assertEqual(self.test_user.oauth_access_token, "token-abc")

    def test_link_user_by_email_no_user_returns_none(self):
        """Returns None without raising when no user matches the email."""
        result = self.env["res.users"]._oauth_link_user_by_email(
            self.provider.id, "sub-x", "unknown@example.com", "token"
        )
        self.assertIsNone(result)

    def test_link_user_by_email_inactive_user_returns_none(self):
        """Inactive users are excluded by the default active_test context."""
        self.test_user.active = False
        result = self.env["res.users"]._oauth_link_user_by_email(
            self.provider.id, "sub-x", "oauth.test@example.com", "token"
        )
        self.assertIsNone(result)

    def test_signin_links_and_returns_login_when_enabled(self):
        """The user is linked on first login."""
        login = self.env["res.users"]._auth_oauth_signin(
            self.provider.id,
            self._make_validation(user_id="sub-first-login"),
            self._make_params(),
        )
        self.assertEqual(login, self.test_user.login)
        self.assertEqual(self.test_user.oauth_uid, "sub-first-login")

    def test_signin_subsequent_login_uses_oauth_uid(self):
        """After the first link, subsequent logins resolve via oauth_uid directly."""
        self.test_user.write(
            {
                "oauth_provider_id": self.provider.id,
                "oauth_uid": "sub-already-set",
            }
        )
        login = self.env["res.users"]._auth_oauth_signin(
            self.provider.id,
            self._make_validation(user_id="sub-already-set"),
            self._make_params(),
        )
        self.assertEqual(login, self.test_user.login)

    def test_signin_no_email_claim_falls_through(self):
        """Without an email claim in the token, auto-link is skipped."""
        ResUsers = self.env["res.users"].with_context(no_user_creation=True)
        result = ResUsers._auth_oauth_signin(
            self.provider.id,
            {"user_id": "sub-no-email"},
            self._make_params(),
        )
        self.assertIsNone(result)
        self.assertFalse(self.test_user.oauth_uid)

    def test_signin_unknown_email_falls_through(self):
        """With an email not present in Odoo, auto-link is skipped."""
        ResUsers = self.env["res.users"].with_context(no_user_creation=True)
        result = ResUsers._auth_oauth_signin(
            self.provider.id,
            self._make_validation(email="nobody@example.com"),
            self._make_params(),
        )
        self.assertIsNone(result)
        self.assertFalse(self.test_user.oauth_uid)

    @mute_logger("odoo.sql_db")
    def test_signin_inactive_user_not_linked(self):
        """An inactive user is not linked → AccessDenied."""
        self.test_user.active = False
        with self.assertRaises(AccessDenied):
            self.env["res.users"]._auth_oauth_signin(
                self.provider.id,
                self._make_validation(),
                self._make_params(),
            )
