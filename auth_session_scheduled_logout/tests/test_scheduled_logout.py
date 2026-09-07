# Copyright 2026 ForgeFlow S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields
from odoo.tests.common import TransactionCase


class TestScheduledLogout(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        group_id = "auth_session_scheduled_logout.group_auth_session_no_sched_logout"
        cls.exempt_group = cls.env.ref(group_id)
        Users = cls.env["res.users"].with_context(no_reset_password=True)
        cls.user = Users.create(
            {
                "name": "Session User",
                "login": "session_user@test.example",
            }
        )
        cls.exempt_user = Users.create(
            {
                "name": "Exempt User",
                "login": "exempt_user@test.example",
                "groups_id": [(4, cls.exempt_group.id)],
            }
        )

    def test_field_not_in_session_token_fields(self):
        # The field must NOT extend the native token formula
        field = self.env["res.users"]._get_session_token_fields()
        self.assertNotIn("auth_session_valid_from", field)

    def test_token_stable_while_timestamp_unset(self):
        # With no timestamp set, the token is the plain one
        # Clearing the timestamp again restores the original token, so on
        # installation, where field is empty everywhere, invalidates nothing
        sid = "a" * 42
        original = self.user._compute_session_token(sid)
        self.user.auth_session_valid_from = fields.Datetime.now()
        self.assertNotEqual(self.user._compute_session_token(sid), original)
        self.user.auth_session_valid_from = False
        self.assertEqual(self.user._compute_session_token(sid), original)

    def test_token_changes_on_revoke(self):
        # Bumping the field creates different token for a given sid
        sid = "a" * 42
        token_before = self.user._compute_session_token(sid)
        self.assertTrue(token_before)
        self.user.auth_session_valid_from = fields.Datetime.now()
        # The value computed for the same sid now differs
        token_after = self.user._compute_session_token(sid)
        self.assertTrue(token_after)
        self.assertNotEqual(token_before, token_after)

    def test_token_false_for_missing_user(self):
        # A stale session cookie may point at a user that no longer exists
        # (e.g. deleted, or rolled back between requests)
        ghost = self.env["res.users"].browse(999999999)
        self.assertFalse(ghost._compute_session_token("a" * 42))

    def test_scope_includes_internal_excludes_exempt(self):
        users = self.env["res.users"]._get_users_to_logout()
        self.assertIn(self.user, users)
        self.assertNotIn(self.exempt_user, users)

    def test_scope_excludes_technical_users(self):
        users = self.env["res.users"]._get_users_to_logout()
        public_user = self.env.ref("base.public_user", raise_if_not_found=False)
        if public_user:
            self.assertNotIn(public_user, users)

    def test_cron_revokes_expected_users(self):
        self.env["res.users"]._cron_revoke_all_sessions()
        self.assertTrue(self.user.auth_session_valid_from)
        self.assertFalse(self.exempt_user.auth_session_valid_from)
