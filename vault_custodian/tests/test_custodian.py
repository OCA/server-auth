# © 2026 Nitrokey GmbH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.exceptions import UserError
from odoo.tests import new_test_user

from odoo.addons.base.tests.common import BaseCommon


class TestCustodian(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.custodian = cls._create_keyed_user("test-vault-custodian")
        cls.owner = cls._create_keyed_user("test-vault-owner")
        cls.env.company.vault_custodian_ids = [(6, 0, cls.custodian.ids)]

    @classmethod
    def _create_keyed_user(cls, login):
        """Create a user with vault keys so it can be used as a custodian."""
        user = new_test_user(cls.env, login=login)
        cls.env["res.users.key"].create(
            {
                "user_id": user.id,
                "public": "a public key",
                "salt": "42",
                "iv": "2424",
                "iterations": 4000,
                "private": "24",
                "current": True,
            }
        )
        return user

    def _owner_right_vals(self):
        return {
            "user_id": self.env.uid,
            "perm_create": True,
            "perm_write": True,
            "perm_delete": True,
            "perm_share": True,
        }

    def _create_vault(self, **vals):
        return self.env["vault"].create({"name": "Vault", **vals})

    def _create_vault_as_owner(self, **vals):
        return self.env["vault"].with_user(self.owner).create({"name": "Vault", **vals})

    def _custodian_right(self, vault, user=None):
        user = user or self.custodian
        return vault.right_ids.filtered(lambda r: r.user_id == user)

    # -- Seeding on vault creation ------------------------------------------

    def test_custodian_added_on_create(self):
        vault = self._create_vault()
        right = self._custodian_right(vault)
        self.assertEqual(right.user_id, self.custodian)
        self.assertTrue(right.perm_share)
        self.assertFalse(right.perm_create)
        self.assertFalse(right.perm_write)
        self.assertFalse(right.perm_delete)

    def test_multiple_custodians_added_on_create(self):
        other = self._create_keyed_user("test-vault-custodian-2")
        self.env.company.vault_custodian_ids = [(6, 0, (self.custodian + other).ids)]
        vault = self._create_vault()
        self.assertIn(self.custodian, vault.right_ids.user_id)
        self.assertIn(other, vault.right_ids.user_id)

    def test_custodian_not_added_to_existing_vault(self):
        # Only future vaults get the custodian; disabling here simulates a
        # vault created before the custodian was configured
        self.env.company.vault_custodian_ids = [(5, 0, 0)]
        vault = self._create_vault()
        self.assertFalse(self._custodian_right(vault))

    def test_owner_as_custodian_no_duplicate(self):
        # If the owner is also a custodian there must be no duplicated right
        self.env.company.vault_custodian_ids = [(6, 0, self.env.user.ids)]
        vault = self._create_vault()
        self.assertEqual(len(vault.right_ids), 1)

    # -- Enforcement on create ----------------------------------------------

    def test_custodian_removed_before_save_is_blocked(self):
        # Removing the default custodian line before the first save (so unlink
        # is never called) must still be prevented on create
        with self.assertRaisesRegex(UserError, "must be shared"):
            self._create_vault(right_ids=[(0, 0, self._owner_right_vals())])

    def test_missing_one_of_multiple_custodians_blocked(self):
        other = self._create_keyed_user("test-vault-custodian-2")
        self.env.company.vault_custodian_ids = [(6, 0, (self.custodian + other).ids)]
        with self.assertRaisesRegex(UserError, "must be shared"):
            self._create_vault(
                right_ids=[
                    (0, 0, self._owner_right_vals()),
                    (0, 0, {"user_id": self.custodian.id, "perm_share": True}),
                ]
            )

    def test_custodian_readd_without_share_is_blocked(self):
        # Re-adding a custodian without the share permission must be blocked
        with self.assertRaisesRegex(UserError, "must have the share permission"):
            self._create_vault(
                right_ids=[
                    (0, 0, self._owner_right_vals()),
                    (0, 0, {"user_id": self.custodian.id, "perm_share": False}),
                ]
            )

    # -- Protection of existing custodian rights ----------------------------

    def test_custodian_cannot_be_removed(self):
        vault = self._create_vault_as_owner()
        right = self._custodian_right(vault)
        with self.assertRaisesRegex(UserError, "can not be removed"):
            right.with_user(self.owner).unlink()

    def test_custodian_cannot_be_removed_by_custodian(self):
        # The custodian itself can not drop its own mandatory right either
        vault = self._create_vault_as_owner()
        right = self._custodian_right(vault)
        with self.assertRaisesRegex(UserError, "can not be removed"):
            right.with_user(self.custodian).unlink()

    def test_custodian_share_cannot_be_removed(self):
        vault = self._create_vault_as_owner()
        right = self._custodian_right(vault)
        with self.assertRaisesRegex(UserError, "share permission"):
            right.with_user(self.owner).perm_share = False

    def test_custodian_user_cannot_be_changed(self):
        vault = self._create_vault_as_owner()
        right = self._custodian_right(vault)
        other = self._create_keyed_user("test-vault-other")
        with self.assertRaisesRegex(UserError, "user of a custodian"):
            right.with_user(self.owner).user_id = other

    def test_custodian_extra_permissions_can_be_granted(self):
        vault = self._create_vault()
        right = self._custodian_right(vault)
        right.write({"perm_write": True, "perm_delete": True})
        self.assertTrue(right.perm_write)
        self.assertTrue(right.perm_delete)

    def test_custodian_removable_as_superuser(self):
        vault = self._create_vault()
        right = self._custodian_right(vault)
        right.sudo().unlink()
        self.assertFalse(right.exists())

    def test_vault_with_custodian_can_be_deleted(self):
        vault = self._create_vault_as_owner()
        right = self._custodian_right(vault)
        vault.with_user(self.owner).unlink()
        self.assertFalse(vault.exists())
        self.assertFalse(right.exists())

    def test_custodian_removable_after_unconfigured(self):
        # Protection is evaluated live: once the user is no longer configured
        # as a custodian the right becomes a normal removable share
        vault = self._create_vault()
        right = self._custodian_right(vault)
        self.env.company.vault_custodian_ids = [(5, 0, 0)]
        right.unlink()
        self.assertFalse(right.exists())

    # -- Configuration validation -------------------------------------------

    def test_keyless_user_cannot_be_custodian(self):
        keyless = new_test_user(self.env, login="test-vault-keyless")
        with self.assertRaisesRegex(UserError, "no vault keys"):
            self.env.company.vault_custodian_ids = [(4, keyless.id)]

    def test_custodian_key_check_ignores_record_rules(self):
        # A user with keys can be set as custodian even when the acting user
        # can not read the custodian's keys due to record rules
        admin = new_test_user(
            self.env, login="test-vault-admin", groups="base.group_system"
        )
        company = self.env.company.with_user(admin)
        company.vault_custodian_ids = [(6, 0, self.custodian.ids)]
        self.assertEqual(company.vault_custodian_ids, self.custodian)

    # -- has_vault_key helper -----------------------------------------------

    def test_has_vault_key_compute(self):
        keyless = new_test_user(self.env, login="test-vault-keyless")
        self.assertTrue(self.custodian.has_vault_key)
        self.assertFalse(keyless.has_vault_key)

    def test_has_vault_key_search(self):
        keyless = new_test_user(self.env, login="test-vault-keyless")
        with_keys = self.env["res.users"].search([("has_vault_key", "=", True)])
        without_keys = self.env["res.users"].search([("has_vault_key", "=", False)])
        self.assertIn(self.custodian, with_keys)
        self.assertNotIn(self.custodian, without_keys)
        self.assertIn(keyless, without_keys)
        self.assertNotIn(keyless, with_keys)
