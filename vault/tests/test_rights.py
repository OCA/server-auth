# © 2021 Florian Kantelberg - initOS GmbH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo.exceptions import AccessError
from odoo.tests import new_test_user

from odoo.addons.base.tests.common import BaseCommon

_logger = logging.getLogger(__name__)


class TestAccessRights(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = new_test_user(
            cls.env,
            login="test-vault-user",
        )
        cls.vault = cls.env["vault"].create({"name": "Vault"})
        cls.entry = cls.env["vault.entry"].create(
            {"vault_id": cls.vault.id, "name": "Entry"}
        )
        cls.field = cls.env["vault.field"].create(
            {"entry_id": cls.entry.id, "name": "Field", "value": "Value"}
        )
        cls.vault.right_ids.write({"key": "Owner"})

    def test_vault_reencrypt(self):
        right = self.env["vault.right"].create(
            {
                "vault_id": self.vault.id,
                "user_id": self.user.id,
                "perm_create": False,
            }
        )

        assert not self.vault.reencrypt_required
        right.unlink()
        assert self.vault.reencrypt_required

    def test_public_key(self):
        key = self.env["res.users.key"].create(
            {
                "user_id": self.vault.user_id.id,
                "public": "a public key",
                "salt": "42",
                "iv": "2424",
                "iterations": 4000,
                "private": "24",
            }
        )
        self.assertTrue(self.vault.right_ids.public_key)
        self.assertEqual(key.public, self.vault.right_ids.public_key)

    def test_owner_access(self):
        # The owner can always access despite the permissions
        for obj in [self.field, self.entry, self.vault]:
            obj.name = "Owned"

            right = self.vault.right_ids
            right.perm_write = False
            obj.name = "Owned"

            right.perm_delete = False
            obj.unlink()

    def test_no_create(self):
        self.env["vault.right"].create(
            {
                "vault_id": self.vault.id,
                "user_id": self.user.id,
                "perm_create": False,
            }
        )

        for obj in [self.field, self.entry, self.vault]:
            with self.assertRaises(AccessError):
                obj.with_user(self.user).check_access("create")

    def test_no_right(self):
        # No right defined for test user means access denied
        for obj in [self.field, self.entry, self.vault]:
            with self.assertRaises(AccessError):
                self.assertTrue(obj.with_user(self.user).read())

            with self.assertRaises(AccessError):
                obj.with_user(self.user).name = "Owned"

            with self.assertRaises(AccessError):
                obj.with_user(self.user).unlink()

    def test_no_permission(self):
        # Defined right but no write permission means access denied
        self.env["vault.right"].create(
            {
                "vault_id": self.vault.id,
                "user_id": self.user.id,
                "perm_create": False,
                "perm_write": False,
                "perm_delete": False,
            }
        )
        for obj in [self.field, self.entry, self.vault]:
            self.assertTrue(obj.with_user(self.user).read())

            with self.assertRaises(AccessError):
                obj.with_user(self.user).name = "Owned"

            with self.assertRaises(AccessError):
                obj.with_user(self.user).unlink()

    def test_granted(self):
        # Granted write permission allows writing
        self.env["vault.right"].create(
            {
                "vault_id": self.vault.id,
                "user_id": self.user.id,
                "perm_write": True,
                "perm_delete": True,
            }
        )
        for obj in [self.field, self.entry, self.vault]:
            self.assertTrue(obj.with_user(self.user).read())

            obj.with_user(self.user).name = "Owned"
            obj.with_user(self.user).unlink()

    def test_owner_share(self):
        self.env["vault.right"].create(
            {"vault_id": self.vault.id, "user_id": self.user.id}
        )

    def test_user_share_no_right(self):
        # No right defined means AccessError
        with self.assertRaises(AccessError):
            self.env["vault.right"].with_user(self.user).create(
                {"vault_id": self.vault.id, "user_id": 2}
            )

    def test_user_share_no_permission(self):
        # Created right but no permission to share
        right = self.env["vault.right"].create(
            {"vault_id": self.vault.id, "user_id": self.user.id, "perm_share": False}
        )

        with self.assertRaises(AccessError):
            right.with_user(self.user).create({"vault_id": self.vault.id, "user_id": 2})

    def test_user_share_granted(self):
        # Granted permission to share
        right = self.env["vault.right"].create(
            {"vault_id": self.vault.id, "user_id": self.user.id, "perm_share": True}
        )
        right.with_user(self.user).create({"vault_id": self.vault.id, "user_id": 2})

        right.unlink()
