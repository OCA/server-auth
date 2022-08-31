# © 2021 Florian Kantelberg - initOS GmbH
# Copyright 2022 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from datetime import datetime

from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase

_logger = logging.getLogger(__name__)


class TestVault(TransactionCase):
    def setUp(self):
        super().setUp()

        self.vault = self.env["vault"].create({"name": "Vault"})
        self.entry = self.env["vault.entry"].create(
            {"vault_id": self.vault.id, "name": "Entry"}
        )
        self.child = self.env["vault.entry"].create(
            {"vault_id": self.vault.id, "name": "Child", "parent_id": self.entry.id}
        )

    def test_entry_path(self):
        self.assertEqual(self.entry.complete_name, "Entry")
        self.assertEqual(self.child.complete_name, "Entry / Child")

    def test_wizard_actions(self):
        values = self.child.action_open_import_wizard()
        self.assertEqual(values["context"]["default_parent_id"], self.child.id)

        values = self.vault.action_open_import_wizard()
        self.assertNotIn("default_parent_id", values["context"])

        values = self.child.action_open_export_wizard()
        self.assertEqual(values["context"]["default_entry_id"], self.child.id)

        values = self.vault.action_open_export_wizard()
        self.assertNotIn("default_entry_id", values["context"])

    def test_master_key(self):
        right = self.vault.right_ids
        self.assertEqual(self.vault.master_key, right.master_key)

        self.vault.master_key = "test"
        self.assertEqual(right.key, "test")

    def test_share_public_key(self):
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

        expected = {"user": 1, "public": key.public}
        self.assertIn(expected, self.vault.share_public_keys())

    def test_keys(self):
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

        self.assertEqual(set("0123456789abcdef:"), set(key.fingerprint))

        key.public = ""
        self.assertEqual(key.fingerprint, False)

    def test_store_keys(self):
        model = self.env["res.users.key"]

        # Raise some errors because of wrong parameters
        with self.assertRaises(ValidationError):
            model.store(1, "iv", "private", "public", 42, 42)

        with self.assertRaises(ValidationError):
            model.store(3000, "iv", "private", "public", "salt", 42)

        with self.assertRaises(ValidationError):
            model.store(4000, "iv", "private", "public", "salt", "abc")

        # Actually store a new key
        uuid = model.store(4000, "iv", "private", "public", "salt", 42)
        rec = model.search([("uuid", "=", uuid)])
        self.assertEqual(rec.private, "private")
        self.assertTrue(rec.current)

        # Don't store the same again
        uuid = model.store(4000, "iv", "private", "public", "salt", 42)
        self.assertFalse(uuid)

        # Store a new one and disable the old one
        uuid = model.store(4000, "iv", "more private", "public", "salt", 42)
        self.assertFalse(rec.current)

        rec = model.search([("uuid", "=", uuid)])
        self.assertEqual(rec.private, "more private")
        self.assertTrue(rec.current)

        # Try to extract the public key again
        user_id = self.env["res.users"].search([], limit=1, order="id DESC").id
        public = model.extract_public_key(user_id + 1)
        self.assertFalse(public)
        public = model.extract_public_key(self.env.uid)
        self.assertEqual(public, "public")

    def test_vault_keys(self):
        keys = self.env.user.get_vault_keys()
        self.assertEqual(keys, {})

        data = {
            "user_id": self.env.user.id,
            "public": "a public key",
            "salt": "42",
            "iv": "2424",
            "iterations": 4000,
            "private": "24",
        }
        self.env["res.users.key"].create(data)

        keys = self.env.user.get_vault_keys()
        for key in ["private", "public", "iv", "salt", "iterations"]:
            self.assertEqual(keys[key], data[key])

    def test_vault_entry_recursion(self):
        child = self.env["vault.entry"].create(
            {"vault_id": self.vault.id, "name": "Entry", "parent_id": self.entry.id}
        )

        with self.assertRaises(ValidationError):
            self.entry.parent_id = child.id

    def test_search_expired(self):
        entry = self.env["vault.entry"]
        self.assertEqual(entry._search_expired("in", []), [])

        domain = entry._search_expired("=", True)
        self.assertEqual(domain[0][:2], ("expire_date", "<"))
        self.assertIsInstance(domain[0][2], datetime)

        domain = entry._search_expired("!=", False)
        self.assertEqual(domain[0][:2], ("expire_date", "<"))
        self.assertIsInstance(domain[0][2], datetime)

        domain = entry._search_expired("=", False)
        self.assertTrue(domain[0] == "|")
        self.assertIn(("expire_date", "=", False), domain)
        self.assertTrue(any(("expire_date", ">=") == d[:2] for d in domain))

    def test_vault_entry_search_panel_limit(self):
        res = self.entry.search_panel_select_range("parent_id")
        total_items = self.env["vault.entry"].search_count([("child_ids", "!=", False)])
        self.assertEqual(len(res["values"]), total_items)
