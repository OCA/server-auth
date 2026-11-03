# © 2024 Odoo Community Association (OCA)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.exceptions import AccessError, ValidationError

from odoo.addons.base.tests.common import BaseCommon


class TestAccessLog(BaseCommon):
    def setUp(self):
        super().setUp()
        self.vault = self.env["vault"].create({"name": "Vault"})
        self.entry = self.env["vault.entry"].create(
            {"vault_id": self.vault.id, "name": "Entry"}
        )
        group_user = self.env.ref("base.group_user")
        self.user_a = self.env["res.users"].create(
            {
                "name": "Vault User A",
                "login": "vault_user_a",
                "groups_id": [(6, 0, [group_user.id])],
            }
        )
        self.user_b = self.env["res.users"].create(
            {
                "name": "Vault User B",
                "login": "vault_user_b",
                "groups_id": [(6, 0, [group_user.id])],
            }
        )

    def test_action_log_access_creates_log(self):
        self.entry.action_log_access("reveal")
        logs = self.env["vault.access.log"].search([("secret_id", "=", self.entry.id)])
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs.access_type, "reveal")
        self.assertEqual(logs.user_id, self.env.user)
        # No HTTP request in tests -> IP resolves to empty, never crashes.
        self.assertFalse(logs.ip_address)

    def test_invalid_access_type_rejected(self):
        with self.assertRaises(ValidationError):
            self.entry.action_log_access("tamper")

    def test_logs_visible_only_to_owner(self):
        Log = self.env["vault.access.log"].sudo()
        Log.create(
            {
                "secret_id": self.entry.id,
                "user_id": self.user_a.id,
                "access_type": "reveal",
            }
        )
        Log.create(
            {
                "secret_id": self.entry.id,
                "user_id": self.user_b.id,
                "access_type": "copy",
            }
        )
        logs_a = self.env["vault.access.log"].with_user(self.user_a).search([])
        self.assertEqual(len(logs_a), 1)
        self.assertEqual(logs_a.user_id, self.user_a)

    def test_logs_are_immutable_for_users(self):
        log = (
            self.env["vault.access.log"]
            .sudo()
            .create(
                {
                    "secret_id": self.entry.id,
                    "user_id": self.user_a.id,
                    "access_type": "reveal",
                }
            )
        )
        with self.assertRaises(AccessError):
            log.with_user(self.user_a).write({"access_type": "copy"})
        with self.assertRaises(AccessError):
            log.with_user(self.user_a).unlink()
