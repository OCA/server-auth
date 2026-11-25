# Copyright 2026 INVITU (<https://www.invitu.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import json
import re

from odoo.tests import HttpCase, JsonRpcException, new_test_user, tagged


def _extract_props(content, component_name):
    """Extract and decode the props of a mounted <owl-component> from raw
    HTML bytes, exactly as the browser's own DOM parser would read them -
    entries are no longer server-rendered as plain HTML, they travel to
    the OWL component as JSON in this attribute."""
    match = re.search(
        rf'<owl-component name="{re.escape(component_name)}" props="([^"]*)"',
        content.decode(),
    )
    assert match, f"owl-component {component_name!r} not found in response"
    from html import unescape

    return json.loads(unescape(match.group(1)))


@tagged("post_install", "-at_install")
class TestPortalHttp(HttpCase):
    """Real HTTP requests, mirroring account/tests/test_portal_invoice.py."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.portal_with_right = new_test_user(
            cls.env, login="portal-http-with-right", groups="base.group_portal"
        )
        cls.portal_without_right = new_test_user(
            cls.env, login="portal-http-without-right", groups="base.group_portal"
        )

        cls.vault = cls.env["vault"].create({"name": "HTTP test vault"})
        tag = cls.env["vault.tag"].create({"name": "HTTP test tag"})
        entry = cls.env["vault.entry"].create(
            {
                "vault_id": cls.vault.id,
                "name": "HTTP test entry",
                "url": "https://example.com",
                "tags": [(6, 0, [tag.id])],
            }
        )
        cls.env["vault.field"].create(
            {"entry_id": entry.id, "name": "HTTP test field", "value": "secret"}
        )
        cls.file = cls.env["vault.file"].create(
            {"entry_id": entry.id, "name": "HTTP test file", "value": "c2VjcmV0"}
        )
        cls.env["vault.right"].create(
            {"vault_id": cls.vault.id, "user_id": cls.portal_with_right.id}
        )

        expired_entry = cls.env["vault.entry"].create(
            {
                "vault_id": cls.vault.id,
                "name": "Expired entry",
                "expire_date": "2000-01-01 00:00:00",
            }
        )
        cls.env["vault.field"].create(
            {"entry_id": expired_entry.id, "name": "field", "value": "secret"}
        )

    def test_portal_my_vaults_page_loads(self):
        self.authenticate(self.portal_with_right.login, self.portal_with_right.login)
        res = self.url_open("/my/vaults")
        self.assertEqual(res.status_code, 200)

    def test_portal_vault_detail_accessible_with_right(self):
        self.authenticate(self.portal_with_right.login, self.portal_with_right.login)
        res = self.url_open(f"/my/vaults/{self.vault.id}")
        self.assertEqual(res.status_code, 200)

        props = _extract_props(res.content, "vault_portal.vault_detail")
        names = {e["name"] for e in props["entries"]}
        self.assertIn("HTTP test entry", names)

        entry = next(e for e in props["entries"] if e["name"] == "HTTP test entry")
        self.assertEqual(entry["url"], "https://example.com")
        self.assertIn("HTTP test tag", entry["tags"])
        self.assertEqual(entry["fields"][0]["name"], "HTTP test field")

        # A file's encrypted content is never embedded in the initial
        # page - only metadata, fetched separately on download.
        self.assertEqual(entry["files"][0]["name"], "HTTP test file")
        self.assertNotIn("value", entry["files"][0])
        self.assertNotIn("iv", entry["files"][0])

    def test_portal_vault_read_file_content(self):
        self.authenticate(self.portal_with_right.login, self.portal_with_right.login)
        result = self.make_jsonrpc_request(
            f"/my/vaults/{self.vault.id}/files/{self.file.id}/content"
        )
        self.assertEqual(result["value"], self.file.value.decode())
        self.assertEqual(result["iv"], self.file.iv)

    def test_portal_vault_read_file_content_blocked_without_right(self):
        self.authenticate(
            self.portal_without_right.login, self.portal_without_right.login
        )
        with self.assertRaises(JsonRpcException):
            self.make_jsonrpc_request(
                f"/my/vaults/{self.vault.id}/files/{self.file.id}/content"
            )

    def test_portal_vault_detail_not_found_without_right(self):
        self.authenticate(
            self.portal_without_right.login, self.portal_without_right.login
        )
        res = self.url_open(f"/my/vaults/{self.vault.id}")
        self.assertEqual(res.status_code, 404)

    def test_portal_vault_detail_not_found_for_nonexistent_id(self):
        self.authenticate(self.portal_with_right.login, self.portal_with_right.login)
        res = self.url_open("/my/vaults/999999")
        self.assertEqual(res.status_code, 404)

    def test_my_counters_includes_vault_count(self):
        self.authenticate(self.portal_with_right.login, self.portal_with_right.login)
        result = self.make_jsonrpc_request(
            "/my/counters", {"counters": ["vault_count"]}
        )
        self.assertEqual(result.get("vault_count"), 1)

    def test_portal_vault_detail_filterby_active(self):
        self.authenticate(self.portal_with_right.login, self.portal_with_right.login)
        res = self.url_open(f"/my/vaults/{self.vault.id}?filterby=active")
        names = {
            e["name"]
            for e in _extract_props(res.content, "vault_portal.vault_detail")["entries"]
        }
        self.assertIn("HTTP test entry", names)
        self.assertNotIn("Expired entry", names)

    def test_portal_vault_detail_filterby_expired(self):
        self.authenticate(self.portal_with_right.login, self.portal_with_right.login)
        res = self.url_open(f"/my/vaults/{self.vault.id}?filterby=expired")
        names = {
            e["name"]
            for e in _extract_props(res.content, "vault_portal.vault_detail")["entries"]
        }
        self.assertIn("Expired entry", names)
        self.assertNotIn("HTTP test entry", names)

    def test_portal_vault_detail_shows_empty_leaf_entry(self):
        # A freshly created entry has no field yet: it must still be
        # visible, or there would be no way to add a first field to it.
        self.env["vault.entry"].create(
            {"vault_id": self.vault.id, "name": "Empty leaf entry"}
        )
        self.authenticate(self.portal_with_right.login, self.portal_with_right.login)
        res = self.url_open(f"/my/vaults/{self.vault.id}")
        names = {
            e["name"]
            for e in _extract_props(res.content, "vault_portal.vault_detail")["entries"]
        }
        self.assertIn("Empty leaf entry", names)

    def test_portal_vault_detail_hides_empty_folder_entry(self):
        # An entry with no field of its own but with a child entry is a
        # pure organizational folder: not sent as its own entry (its
        # child is, carrying the folder's name as parentName instead).
        folder = self.env["vault.entry"].create(
            {"vault_id": self.vault.id, "name": "Folder entry"}
        )
        child = self.env["vault.entry"].create(
            {
                "vault_id": self.vault.id,
                "parent_id": folder.id,
                "name": "Child entry",
            }
        )
        self.env["vault.field"].create(
            {"entry_id": child.id, "name": "field", "value": "secret"}
        )
        self.authenticate(self.portal_with_right.login, self.portal_with_right.login)
        res = self.url_open(f"/my/vaults/{self.vault.id}")
        props = _extract_props(res.content, "vault_portal.vault_detail")

        names = {e["name"] for e in props["entries"]}
        self.assertIn("Child entry", names)
        self.assertNotIn("Folder entry", names)

        child_entry = next(e for e in props["entries"] if e["name"] == "Child entry")
        self.assertEqual(child_entry["parentName"], "Folder entry")
