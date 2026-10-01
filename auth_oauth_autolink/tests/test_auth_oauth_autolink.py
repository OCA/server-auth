# Copyright 2026 Nimarosa
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import json
from unittest.mock import patch

from odoo.exceptions import AccessDenied
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestAuthOauthAutolink(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Signup must stay closed (B2B): that is the production setup this
        # module exists for, and it makes the stock sign-in deterministically
        # raise AccessDenied instead of creating a duplicate user.
        cls.env["ir.config_parameter"].sudo().set_param(
            "auth_signup.invitation_scope", "b2b"
        )
        cls.provider = cls.env.ref("auth_oauth.provider_google")
        cls.provider.write({"enabled": True, "autolink_by_email": True})
        cls.other_provider = cls.env["auth.oauth.provider"].create(
            {
                "name": "Other provider",
                "auth_endpoint": "https://example.invalid/auth",
                "validation_endpoint": "https://example.invalid/userinfo",
                "body": "Log in with Other",
                "autolink_by_email": False,
            }
        )
        cls.user = cls.env["res.users"].create(
            {"name": "Ana Perez", "login": "ana.perez@example.com"}
        )

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------
    def _validation(self, email="ana.perez@example.com", uid="google-uid-1", **kw):
        validation = {"user_id": uid, "email": email, "email_verified": True}
        validation.update(kw)
        return validation

    def _params(self, access_token="token-1"):
        return {
            "access_token": access_token,
            "state": json.dumps({"d": self.env.cr.dbname, "p": self.provider.id}),
        }

    def _autolink(self, validation=None, provider=None):
        """Drive the link exactly where ``_auth_oauth_validate`` drives it."""
        return (
            self.env["res.users"]
            .sudo()
            ._auth_oauth_autolink(
                (provider or self.provider).id,
                validation if validation is not None else self._validation(),
            )
        )

    def _signin(self, validation=None, params=None, provider=None):
        return (
            self.env["res.users"]
            .sudo()
            ._auth_oauth_signin(
                (provider or self.provider).id,
                validation if validation is not None else self._validation(),
                params or self._params(),
            )
        )

    def _messages(self, user):
        return self.env["mail.message"].search(
            [("model", "=", "res.partner"), ("res_id", "=", user.partner_id.id)]
        )

    def _skip_if_logins_are_lowercased(self):
        """``auth_user_case_insensitive`` makes mixed-case logins impossible.

        It is part of this same repository, so it is installed in the
        all-addons CI job; when it is, a login that differs only in case
        cannot exist and these two scenarios are unreachable by construction.
        """
        installed = (
            self.env["ir.module.module"]
            .sudo()
            .search_count(
                [
                    ("name", "=", "auth_user_case_insensitive"),
                    ("state", "=", "installed"),
                ]
            )
        )
        if installed:
            self.skipTest("auth_user_case_insensitive forces logins to lowercase")

    # ------------------------------------------------------------------
    # happy path
    # ------------------------------------------------------------------
    def test_links_existing_user_by_verified_email(self):
        messages_before = self._messages(self.user)

        linked = self._autolink()

        self.assertEqual(linked, self.user)
        self.assertEqual(self.user.oauth_uid, "google-uid-1")
        self.assertEqual(self.user.oauth_provider_id, self.provider)
        new_messages = self._messages(self.user) - messages_before
        self.assertEqual(len(new_messages), 1, "a chatter note must be logged")
        self.assertIn("Google", new_messages.body)

    def test_validation_links_and_then_sign_in_succeeds(self):
        """The real entry point: validate (which links) then sign in.

        ``_auth_oauth_rpc`` is the only piece that would talk to the provider,
        so it is the only thing mocked; everything below it is the stock code
        path, including whatever else overrides ``_auth_oauth_signin``.
        """
        users = self.env["res.users"].sudo()
        with patch.object(
            type(users), "_auth_oauth_rpc", return_value=self._validation()
        ):
            validation = users._auth_oauth_validate(self.provider.id, "token-1")

        self.assertEqual(validation["user_id"], "google-uid-1")
        self.assertEqual(self.user.oauth_uid, "google-uid-1")
        self.assertEqual(self.user.oauth_provider_id, self.provider)
        self.assertEqual(
            self._signin(validation=validation), self.user.login, "sign-in must follow"
        )

    def test_linked_user_can_then_sign_in(self):
        self._autolink()

        self.assertEqual(self._signin(), self.user.login)

    def test_second_login_does_not_link_again(self):
        self._autolink()
        messages_after_link = self._messages(self.user)

        self.assertFalse(
            self._autolink(), "an already-linked identity must not be relinked"
        )

        self.assertEqual(self.user.oauth_uid, "google-uid-1")
        self.assertEqual(
            self._messages(self.user),
            messages_after_link,
            "the autolink note must be posted only once",
        )

    def test_email_match_is_case_insensitive(self):
        self._skip_if_logins_are_lowercased()
        self.user.login = "Ana.Perez@Example.com"

        linked = self._autolink(
            validation=self._validation(email="ANA.perez@example.COM")
        )

        self.assertEqual(linked, self.user)
        self.assertEqual(self.user.oauth_uid, "google-uid-1")

    def test_claim_is_normalized_against_a_lowercase_login(self):
        """The claim's case never matters, whatever the login looks like."""
        linked = self._autolink(
            validation=self._validation(email="ANA.PEREZ@EXAMPLE.COM")
        )

        self.assertEqual(linked, self.user)

    # ------------------------------------------------------------------
    # refusals -- every one of them must leave the stock behaviour alone
    # ------------------------------------------------------------------
    def _assert_refused(self, **kw):
        self.assertFalse(self._autolink(**kw), "nothing may be linked")
        with self.assertRaises(AccessDenied):
            self._signin(**kw)

    def test_provider_flag_off_does_not_link(self):
        self.provider.autolink_by_email = False

        self._assert_refused()

        self.assertFalse(self.user.oauth_uid)

    def test_unverified_email_does_not_link(self):
        self._assert_refused(validation=self._validation(email_verified=False))
        self.assertFalse(self.user.oauth_uid)

    def test_missing_verified_claim_does_not_link(self):
        validation = self._validation()
        del validation["email_verified"]

        self._assert_refused(validation=validation)

        self.assertFalse(self.user.oauth_uid)

    def test_legacy_verified_email_claim_spelling_is_accepted(self):
        validation = self._validation()
        del validation["email_verified"]
        validation["verified_email"] = "true"

        linked = self._autolink(validation=validation)

        self.assertEqual(linked, self.user)
        self.assertEqual(self.user.oauth_uid, "google-uid-1")

    def test_no_email_claim_does_not_link(self):
        validation = self._validation()
        del validation["email"]

        self._assert_refused(validation=validation)

    def test_no_matching_user_does_not_link(self):
        self._assert_refused(validation=self._validation(email="nobody@example.com"))

    def test_already_linked_user_is_never_overwritten(self):
        self.user.write(
            {"oauth_provider_id": self.other_provider.id, "oauth_uid": "other-uid"}
        )

        self._assert_refused()

        self.assertEqual(self.user.oauth_uid, "other-uid")
        self.assertEqual(self.user.oauth_provider_id, self.other_provider)

    def test_inactive_user_is_not_linked(self):
        self.user.active = False

        self._assert_refused()

        self.assertFalse(self.user.oauth_uid)

    def test_ambiguous_email_does_not_link(self):
        self._skip_if_logins_are_lowercased()
        twin = self.env["res.users"].create(
            {"name": "Ana Perez (twin)", "login": "ANA.PEREZ@example.com"}
        )

        self._assert_refused()

        self.assertFalse(self.user.oauth_uid)
        self.assertFalse(twin.oauth_uid)
