# Copyright 2026 INVITU (<https://www.invitu.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.exceptions import AccessError, ValidationError
from odoo.tests import new_test_user

from odoo.addons.base.tests.common import BaseCommon


class TestPortalAccess(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.portal_a = new_test_user(
            cls.env, login="portal-client-a", groups="base.group_portal"
        )
        cls.portal_b = new_test_user(
            cls.env, login="portal-client-b", groups="base.group_portal"
        )

        cls.vault_a = cls.env["vault"].create({"name": "Client A"})
        cls.entry_a = cls.env["vault.entry"].create(
            {"vault_id": cls.vault_a.id, "name": "Entry A"}
        )
        cls.field_a = cls.env["vault.field"].create(
            {"entry_id": cls.entry_a.id, "name": "Field A", "value": "Value A"}
        )
        cls.file_a = cls.env["vault.file"].create(
            {"entry_id": cls.entry_a.id, "name": "File A", "value": "ZmFrZQ=="}
        )

        cls.vault_b = cls.env["vault"].create({"name": "Client B"})
        cls.entry_b = cls.env["vault.entry"].create(
            {"vault_id": cls.vault_b.id, "name": "Entry B"}
        )

        # Explicit default: MFA-policy tests below set their own value.
        cls.env["ir.config_parameter"].sudo().set_param(
            "vault_portal.mfa_policy", "none"
        )

    def _enable_totp(self, user):
        user.sudo().totp_secret = "AAAAAAAAAAAAAAAA"

    def test_portal_no_right_no_access(self):
        for obj in [self.vault_a, self.entry_a, self.field_a, self.file_a]:
            with self.assertRaises(AccessError):
                obj.with_user(self.portal_a).read()

        self.assertEqual(self.env["vault"].with_user(self.portal_a).search_count([]), 0)

    def test_portal_no_cross_client_read(self):
        self.env["vault.right"].create(
            {"vault_id": self.vault_a.id, "user_id": self.portal_a.id}
        )

        self.assertTrue(self.entry_a.with_user(self.portal_a).read(["name"]))

        with self.assertRaises(AccessError):
            self.entry_b.with_user(self.portal_a).read()

        visible_vaults = self.env["vault"].with_user(self.portal_a).search([])
        self.assertEqual(visible_vaults, self.vault_a)
        self.assertNotIn(self.vault_b, visible_vaults)

    def test_portal_readonly_enforced(self):
        self.env["vault.right"].create(
            {
                "vault_id": self.vault_a.id,
                "user_id": self.portal_a.id,
                "perm_write": False,
                "perm_create": False,
                "perm_delete": False,
            }
        )

        self.assertTrue(self.entry_a.with_user(self.portal_a).read(["name"]))

        with self.assertRaises(AccessError):
            self.entry_a.with_user(self.portal_a).name = "Tampered"

        with self.assertRaises(AccessError):
            self.entry_a.with_user(self.portal_a).unlink()

    def test_portal_vault_and_entry_rename_delete_always_blocked(self):
        self.env["vault.right"].create(
            {
                "vault_id": self.vault_a.id,
                "user_id": self.portal_a.id,
                "perm_write": True,
                "perm_create": True,
                "perm_delete": True,
            }
        )

        self.assertTrue(self.entry_a.with_user(self.portal_a).read(["name"]))

        with self.assertRaises(AccessError):
            self.entry_a.with_user(self.portal_a).name = "Should never work"

        with self.assertRaises(AccessError):
            self.entry_a.with_user(self.portal_a).unlink()

        with self.assertRaises(AccessError):
            self.vault_a.with_user(self.portal_a).name = "Should never work either"

    def test_portal_entry_create_blocked_without_permission(self):
        self.env["vault.right"].create(
            {
                "vault_id": self.vault_a.id,
                "user_id": self.portal_a.id,
                "perm_create": False,
            }
        )

        with self.assertRaises(AccessError):
            self.env["vault.entry"].with_user(self.portal_a).create(
                {"vault_id": self.vault_a.id, "name": "Should not be created"}
            )

    def test_portal_entry_create_allowed_with_permission(self):
        self.env["vault.right"].create(
            {
                "vault_id": self.vault_a.id,
                "user_id": self.portal_a.id,
                "perm_create": True,
            }
        )

        entry = (
            self.env["vault.entry"]
            .with_user(self.portal_a)
            .create({"vault_id": self.vault_a.id, "name": "New entry"})
        )
        self.assertEqual(entry.vault_id, self.vault_a)

    def test_portal_entry_create_blocked_on_foreign_vault(self):
        self.env["vault.right"].create(
            {
                "vault_id": self.vault_a.id,
                "user_id": self.portal_a.id,
                "perm_create": True,
            }
        )

        with self.assertRaises(AccessError):
            self.env["vault.entry"].with_user(self.portal_a).create(
                {"vault_id": self.vault_b.id, "name": "Forged"}
            )

    def test_portal_entry_write_url_and_expire_allowed_with_permission(self):
        self.env["vault.right"].create(
            {
                "vault_id": self.vault_a.id,
                "user_id": self.portal_a.id,
                "perm_write": True,
            }
        )

        self.entry_a.with_user(self.portal_a).write(
            {"url": "https://example.com", "expire_date": "2030-01-01 00:00:00"}
        )
        self.assertEqual(self.entry_a.url, "https://example.com")

    def test_portal_entry_write_mixed_fields_blocked(self):
        self.env["vault.right"].create(
            {
                "vault_id": self.vault_a.id,
                "user_id": self.portal_a.id,
                "perm_write": True,
            }
        )

        with self.assertRaises(AccessError):
            self.entry_a.with_user(self.portal_a).write(
                {"url": "https://example.com", "name": "Renamed"}
            )
        self.assertNotEqual(self.entry_a.name, "Renamed")

    def test_portal_field_write_blocked_without_permission(self):
        self.env["vault.right"].create(
            {
                "vault_id": self.vault_a.id,
                "user_id": self.portal_a.id,
                "perm_write": False,
            }
        )

        self.assertTrue(self.field_a.with_user(self.portal_a).read())

        with self.assertRaises(AccessError):
            self.field_a.with_user(self.portal_a).value = "Tampered"

    def test_portal_field_write_allowed_with_permission(self):
        # perm_create/perm_delete forced False: _get_is_owner() would
        # otherwise default them True here.
        self.env["vault.right"].create(
            {
                "vault_id": self.vault_a.id,
                "user_id": self.portal_a.id,
                "perm_write": True,
                "perm_create": False,
                "perm_delete": False,
            }
        )

        self.field_a.with_user(self.portal_a).value = "Updated by client"
        self.assertEqual(self.field_a.value, "Updated by client")

        # Still no create/unlink on vault.field from the portal.
        with self.assertRaises(AccessError):
            self.field_a.with_user(self.portal_a).unlink()

        with self.assertRaises(AccessError):
            self.env["vault.field"].with_user(self.portal_a).create(
                {"entry_id": self.entry_a.id, "name": "New", "value": "x"}
            )

    def test_portal_field_create_blocked_without_permission(self):
        self.env["vault.right"].create(
            {
                "vault_id": self.vault_a.id,
                "user_id": self.portal_a.id,
                "perm_create": False,
            }
        )

        with self.assertRaises(AccessError):
            self.env["vault.field"].with_user(self.portal_a).create(
                {"entry_id": self.entry_a.id, "name": "New", "value": "x"}
            )

    def test_portal_field_create_allowed_with_permission(self):
        self.env["vault.right"].create(
            {
                "vault_id": self.vault_a.id,
                "user_id": self.portal_a.id,
                "perm_create": True,
            }
        )

        new_field = (
            self.env["vault.field"]
            .with_user(self.portal_a)
            .create(
                {"entry_id": self.entry_a.id, "name": "New login", "value": "secret"}
            )
        )
        self.assertEqual(new_field.entry_id, self.entry_a)

    def test_portal_field_create_blocked_on_foreign_vault(self):
        self.env["vault.right"].create(
            {
                "vault_id": self.vault_a.id,
                "user_id": self.portal_a.id,
                "perm_create": True,
            }
        )

        with self.assertRaises(AccessError):
            self.env["vault.field"].with_user(self.portal_a).create(
                {"entry_id": self.entry_b.id, "name": "Forged", "value": "x"}
            )

    def test_portal_field_no_unlink(self):
        self.env["vault.right"].create(
            {
                "vault_id": self.vault_a.id,
                "user_id": self.portal_a.id,
                "perm_write": True,
                "perm_create": True,
                "perm_delete": True,
            }
        )

        with self.assertRaises(AccessError):
            self.field_a.with_user(self.portal_a).unlink()

    def test_portal_file_create_allowed_with_permission(self):
        self.env["vault.right"].create(
            {
                "vault_id": self.vault_a.id,
                "user_id": self.portal_a.id,
                "perm_create": True,
            }
        )

        vault_file = (
            self.env["vault.file"]
            .with_user(self.portal_a)
            .create(
                {"entry_id": self.entry_a.id, "name": "New file", "value": "ZmFrZQ=="}
            )
        )
        self.assertEqual(vault_file.entry_id, self.entry_a)

    def test_portal_file_create_blocked_without_permission(self):
        self.env["vault.right"].create(
            {
                "vault_id": self.vault_a.id,
                "user_id": self.portal_a.id,
                "perm_create": False,
            }
        )

        with self.assertRaises(AccessError):
            self.env["vault.file"].with_user(self.portal_a).create(
                {"entry_id": self.entry_a.id, "name": "x", "value": "ZmFrZQ=="}
            )

    def test_portal_file_create_blocked_on_foreign_vault(self):
        self.env["vault.right"].create(
            {
                "vault_id": self.vault_a.id,
                "user_id": self.portal_a.id,
                "perm_create": True,
            }
        )

        with self.assertRaises(AccessError):
            self.env["vault.file"].with_user(self.portal_a).create(
                {"entry_id": self.entry_b.id, "name": "Forged", "value": "ZmFrZQ=="}
            )

    def test_portal_file_no_write_no_unlink(self):
        self.env["vault.right"].create(
            {
                "vault_id": self.vault_a.id,
                "user_id": self.portal_a.id,
                "perm_write": True,
                "perm_create": True,
                "perm_delete": True,
            }
        )

        with self.assertRaises(AccessError):
            self.file_a.with_user(self.portal_a).name = "Renamed"

        with self.assertRaises(AccessError):
            self.file_a.with_user(self.portal_a).unlink()

    def test_portal_revocation_effective(self):
        right = self.env["vault.right"].create(
            {"vault_id": self.vault_a.id, "user_id": self.portal_a.id}
        )
        self.assertTrue(self.entry_a.with_user(self.portal_a).read(["name"]))

        self.assertFalse(self.vault_a.reencrypt_required)
        right.unlink()
        self.assertTrue(self.vault_a.reencrypt_required)

        with self.assertRaises(AccessError):
            self.entry_a.with_user(self.portal_a).read()

    def test_no_mail_sent_on_entry_write(self):
        message_count_before = self.env["mail.message"].search_count([])

        entry = self.env["vault.entry"].create(
            {"vault_id": self.vault_a.id, "name": "Silent entry"}
        )
        entry.name = "Silent entry, updated"

        message_count_after = self.env["mail.message"].search_count([])
        self.assertEqual(message_count_before, message_count_after)

    def test_portal_can_manage_own_key_pair(self):
        key = (
            self.env["res.users.key"]
            .with_user(self.portal_a)
            .create(
                {
                    "user_id": self.portal_a.id,
                    "public": "a public key",
                    "salt": "42",
                    "iv": "2424",
                    "iterations": 600001,
                    "private": "encrypted private key material",
                    "version": 1,
                }
            )
        )
        self.assertTrue(key.with_user(self.portal_a).read())
        key.with_user(self.portal_a).current = False

    def test_portal_cannot_read_other_users_key(self):
        other_key = self.env["res.users.key"].create(
            {
                "user_id": self.portal_b.id,
                "public": "b's public key",
                "salt": "42",
                "iv": "2424",
                "iterations": 600001,
                "private": "b's encrypted private key",
                "version": 1,
            }
        )
        with self.assertRaises(AccessError):
            other_key.with_user(self.portal_a).read()

    # -- MFA policy: "write" ------------------------------------------

    def test_mfa_policy_write_blocks_write_grant_without_totp(self):
        self.env["ir.config_parameter"].sudo().set_param(
            "vault_portal.mfa_policy", "write"
        )
        with self.assertRaises(ValidationError):
            self.env["vault.right"].create(
                {
                    "vault_id": self.vault_a.id,
                    "user_id": self.portal_a.id,
                    "perm_write": True,
                }
            )

    def test_mfa_policy_write_allows_read_only_grant_without_totp(self):
        # Under the "write" policy, a pure read-only grant is unaffected:
        # 2FA is only required for write/create.
        self.env["ir.config_parameter"].sudo().set_param(
            "vault_portal.mfa_policy", "write"
        )
        self.env["vault.right"].create(
            {
                "vault_id": self.vault_a.id,
                "user_id": self.portal_a.id,
                "perm_write": False,
                "perm_create": False,
            }
        )
        self.assertTrue(self.entry_a.with_user(self.portal_a).read(["name"]))

    def test_mfa_policy_write_allows_write_grant_with_totp(self):
        self.env["ir.config_parameter"].sudo().set_param(
            "vault_portal.mfa_policy", "write"
        )
        self._enable_totp(self.portal_a)
        right = self.env["vault.right"].create(
            {
                "vault_id": self.vault_a.id,
                "user_id": self.portal_a.id,
                "perm_write": True,
            }
        )
        self.assertTrue(right.perm_write)

    def test_mfa_policy_write_disabling_totp_downgrades_to_readonly(self):
        self.env["ir.config_parameter"].sudo().set_param(
            "vault_portal.mfa_policy", "write"
        )
        self._enable_totp(self.portal_a)
        right = self.env["vault.right"].create(
            {
                "vault_id": self.vault_a.id,
                "user_id": self.portal_a.id,
                "perm_write": True,
                "perm_create": True,
            }
        )

        self.portal_a.sudo().totp_secret = False

        right.invalidate_recordset()
        self.assertFalse(right.perm_write)
        self.assertFalse(right.perm_create)
        # Read access is preserved under the "write" policy.
        self.assertTrue(self.entry_a.with_user(self.portal_a).read(["name"]))

    def test_mfa_policy_write_disabling_totp_on_readonly_right_has_no_effect(self):
        self.env["ir.config_parameter"].sudo().set_param(
            "vault_portal.mfa_policy", "write"
        )
        right = self.env["vault.right"].create(
            {
                "vault_id": self.vault_a.id,
                "user_id": self.portal_a.id,
                "perm_write": False,
                "perm_create": False,
            }
        )
        self._enable_totp(self.portal_a)

        self.portal_a.sudo().totp_secret = False

        self.assertTrue(right.exists())
        self.assertTrue(self.entry_a.with_user(self.portal_a).read(["name"]))

    # -- MFA policy: "read" --------------------------------------------

    def test_mfa_policy_read_blocks_any_grant_without_totp(self):
        self.env["ir.config_parameter"].sudo().set_param(
            "vault_portal.mfa_policy", "read"
        )
        with self.assertRaises(ValidationError):
            self.env["vault.right"].create(
                {
                    "vault_id": self.vault_a.id,
                    "user_id": self.portal_a.id,
                    "perm_write": False,
                    "perm_create": False,
                }
            )

    def test_mfa_policy_read_allows_grant_with_totp(self):
        self.env["ir.config_parameter"].sudo().set_param(
            "vault_portal.mfa_policy", "read"
        )
        self._enable_totp(self.portal_a)
        self.env["vault.right"].create(
            {
                "vault_id": self.vault_a.id,
                "user_id": self.portal_a.id,
                "perm_write": False,
                "perm_create": False,
            }
        )
        self.assertTrue(self.entry_a.with_user(self.portal_a).read(["name"]))

    def test_mfa_policy_read_disabling_totp_revokes_everything(self):
        self.env["ir.config_parameter"].sudo().set_param(
            "vault_portal.mfa_policy", "read"
        )
        self._enable_totp(self.portal_a)
        self.env["vault.right"].create(
            {
                "vault_id": self.vault_a.id,
                "user_id": self.portal_a.id,
                "perm_write": False,
                "perm_create": False,
            }
        )
        self.assertTrue(self.entry_a.with_user(self.portal_a).read(["name"]))

        self.assertFalse(self.vault_a.reencrypt_required)
        self.portal_a.sudo().totp_secret = False
        self.assertTrue(self.vault_a.reencrypt_required)

        with self.assertRaises(AccessError):
            self.entry_a.with_user(self.portal_a).read()

    # -- MFA policy: "none" ---------------------------------------------

    def test_mfa_policy_none_disabling_totp_has_no_effect(self):
        self._enable_totp(self.portal_a)
        right = self.env["vault.right"].create(
            {
                "vault_id": self.vault_a.id,
                "user_id": self.portal_a.id,
                "perm_write": True,
            }
        )

        self.portal_a.sudo().totp_secret = False

        right.invalidate_recordset()
        self.assertTrue(right.perm_write)
        self.assertTrue(self.entry_a.with_user(self.portal_a).read(["name"]))
