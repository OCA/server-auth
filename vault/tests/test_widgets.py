# © 2021 Florian Kantelberg - initOS GmbH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import json
import logging
from uuid import uuid4

from odoo.exceptions import UserError

from odoo.addons.base.tests.common import BaseCommon

_logger = logging.getLogger(__name__)


TestChild = {
    "uuid": "42a",
    "note": "test note child",
    "name": "test child",
    "url": "child.example.org",
    "fields": [],
    "files": [],
    "childs": [],
}

TestData = [
    {
        "uuid": "42b",
        "note": "test note child",
        "name": "don't import",
        "url": "child.example.org",
        "fields": [],
        "files": [],
        "childs": [],
    },
    TestChild,
    {
        "uuid": "42",
        "note": "test note",
        "name": "test name",
        "url": "test.example.org",
        "fields": [
            {"name": "a", "value": "Hello World", "iv": "abcd"},
            {"name": "secret", "value": "dlrow olleh", "iv": "abcd"},
            {"name": "secret", "value": "dlrow olle", "iv": "abcd"},
        ],
        "files": [
            {"name": "a", "value": "Hello World", "iv": "abcd"},
            {"name": "secret", "value": "dlrow olleh", "iv": "abcd"},
            {},
        ],
        "childs": [
            {
                "uuid": "42aa",
                "note": "test note subchild",
                "name": "test subchild",
                "url": "subchild.example.org",
                "fields": [],
                "files": [],
                "childs": [],
            },
            TestChild,
        ],
    },
    TestChild,
]


class TestWidgets(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.vault = cls.env["vault"].create({"name": "Vault"})
        cls.entry = cls.env["vault.entry"].create(
            {"vault_id": cls.vault.id, "name": "Entry"}
        )

    def test_path_generation(self):
        wiz = self.env["vault.import.wizard"].create(
            {"vault_id": self.vault.id, "crypted_content": json.dumps(TestData)}
        )
        wiz._onchange_content()

        paths = wiz.path.search([("uuid", "=", wiz.uuid)]).mapped("name")

        self.assertEqual(len(paths), 6)
        self.assertIn("test name / test child", paths)
        self.assertIn("test child", paths)
        self.assertIn("test name", paths)

    def test_import(self):
        uuid = uuid4()
        path = self.env["vault.import.wizard.path"].create(
            {"name": "test", "uuid": uuid}
        )

        wiz = self.env["vault.import.wizard"].create(
            {
                "vault_id": self.vault.id,
                "crypted_content": json.dumps(TestData),
                "path": path.id,
                "uuid": uuid,
            }
        )

        wiz.action_import()

        # We have duplicates
        uuids = {"42", "42a", "42aa", self.entry.uuid}
        self.assertSetEqual(set(self.vault.entry_ids.mapped("uuid")), uuids)

        # Creation is depth-first which will cause the 42a to move up
        self.assertEqual(self.vault.entry_ids.mapped("child_ids.uuid"), ["42aa"])

        # This will cause an overwrite of the field
        domain = [("entry_id.uuid", "=", "42"), ("name", "=", "secret")]
        rec = self.env["vault.field"].search(domain)
        self.assertEqual(rec.mapped("value"), ["dlrow olle"])

        # Field with missing keys should fail
        with self.assertRaises(UserError):
            TestChild["fields"].append({"name": "12", "value": "eulav"})
            wiz.crypted_content = json.dumps([TestChild])
            wiz.action_import()

    def test_export(self):
        child = self.env["vault.entry"].create(
            {"vault_id": self.vault.id, "name": "Child", "parent_id": self.entry.id}
        )

        second = self.env["vault.entry"].create(
            {"vault_id": self.vault.id, "name": "second"}
        )

        wiz = self.env["vault.export.wizard"].create({"vault_id": self.vault.id})

        # Export without entry should export entire vault
        wiz._onchange_content()
        entries = json.loads(wiz.content)
        self.assertEqual({e["uuid"] for e in entries}, {second.uuid, self.entry.uuid})
        self.assertEqual(len(entries), 2)

        wiz.entry_id = self.entry

        # Export the entire tree
        wiz._onchange_content()
        entries = json.loads(wiz.content)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["uuid"], self.entry.uuid)
        self.assertEqual(entries[0]["childs"][0]["uuid"], child.uuid)

        # Skip exporting childs
        wiz.include_childs = False
        wiz._onchange_content()
        entries = json.loads(wiz.content)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["uuid"], self.entry.uuid)
        self.assertEqual(len(entries[0]["childs"]), 0)
