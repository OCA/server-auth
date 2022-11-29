# © 2021 Florian Kantelberg - initOS GmbH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from unittest.mock import MagicMock

from odoo.tests import TransactionCase
from odoo.tools import mute_logger

from odoo.addons.website.tools import MockRequest

from ..controllers import main

_logger = logging.getLogger(__name__)


class TestController(TransactionCase):
    def setUp(self):
        super().setUp()

        self.controller = main.Controller()

        self.user = self.env["res.users"].create(
            {"login": "test", "email": "test@test", "name": "test"}
        )
        self.user.inbox_token = "42"
        self.user.keys.current = False
        self.key = self.env["res.users.key"].create(
            {
                "user_id": self.user.id,
                "public": "a public key",
                "salt": "42",
                "iv": "2424",
                "iterations": 4000,
                "private": "24",
                "current": True,
            }
        )
        self.inbox = self.env["vault.inbox"].create(
            {
                "user_id": self.user.id,
                "name": "Inbox",
                "key": "4",
                "iv": "1",
                "secret": "old secret",
                "secret_file": "old file",
                "accesses": 100,
            }
        )

    @mute_logger("odoo.sql_db")
    def test_vault_inbox(self):
        def return_context(template, context):
            self.assertEqual(template, "vault.inbox")
            return context

        with MockRequest(self.env) as request_mock:
            request_mock.render.side_effect = return_context
            response = self.controller.vault_inbox("")
            self.assertIn("error", response)

            response = self.controller.vault_inbox(self.user.inbox_token)
            self.assertNotIn("error", response)
            self.assertEqual(response["public"], self.user.active_key.public)

            # Try to eliminate each error step by step
            request_mock.httprequest.method = "POST"
            request_mock.params = {}
            response = self.controller.vault_inbox(self.user.inbox_token)
            self.assertIn("error", response)

            request_mock.params["name"] = "test"
            response = self.controller.vault_inbox(self.user.inbox_token)
            self.assertIn("error", response)

            request_mock.params.update(
                {"encrypted": "secret", "encrypted_file": "file"}
            )
            response = self.controller.vault_inbox(self.user.inbox_token)
            self.assertIn("error", response)

            request_mock.params["filename"] = "filename"
            response = self.controller.vault_inbox(self.user.inbox_token)
            self.assertIn("error", response)

            self.assertEqual(self.inbox.secret, "old secret")
            self.assertEqual(self.inbox.secret_file, b"old file")

            # Store something successfully
            request_mock.params.update({"iv": "iv", "key": "key"})
            response = self.controller.vault_inbox(self.inbox.token)
            self.assertNotIn("error", response)
            self.assertEqual(self.inbox.secret, "secret")
            self.assertEqual(self.inbox.secret_file, b"file")

            # Test a duplicate inbox
            self.inbox.copy().token = self.inbox.token
            response = self.controller.vault_inbox(self.inbox.token)
            self.assertIn("error", response)

            def raise_error(*args, **kwargs):
                raise TypeError()

            # Catch internal errors
            try:
                request_mock.httprequest.remote_addr = "127.0.0.1"
                self.env["vault.inbox"]._patch_method("store_in_inbox", raise_error)
                response = self.controller.vault_inbox(self.user.inbox_token)
            finally:
                self.env["vault.inbox"]._revert_method("store_in_inbox")

            self.assertIn("error", response)

    @mute_logger("odoo.sql_db")
    def test_vault_public(self):
        with MockRequest(self.env):
            no_key = self.env["res.users"].create(
                {"login": "keyless", "email": "test@test", "name": "test"}
            )

            response = self.controller.vault_public(user_id=no_key.id)
            self.assertEqual(response, {})

            response = self.controller.vault_public(user_id=self.user.id)
            self.assertEqual(response["public_key"], self.key.public)

    @mute_logger("odoo.sql_db")
    def test_vault_store(
        self,
    ):
        with MockRequest(self.env):
            mock = MagicMock()
            try:
                self.env["res.users.key"]._patch_method("store", mock)
                self.controller.vault_store_keys()
                mock.assert_called_once()
            finally:
                self.env["res.users.key"]._revert_method("store")

    @mute_logger("odoo.sql_db")
    def test_vault_keys_get(self):
        with MockRequest(self.env):
            mock = MagicMock()
            try:
                self.env["res.users"]._patch_method("get_vault_keys", mock)
                self.controller.vault_get_keys()
                mock.assert_called_once()
            finally:
                self.env["res.users"]._revert_method("get_vault_keys")

    @mute_logger("odoo.sql_db")
    def test_vault_right_keys(self):
        with MockRequest(self.env):
            self.assertFalse(self.controller.vault_get_right_keys())

            # New vault with user as owner and only right
            vault = self.env["vault"].create({"name": "Vault"})

            response = self.controller.vault_get_right_keys()
            self.assertEqual(response, {vault.uuid: vault.right_ids.key})

    @mute_logger("odoo.sql_db")
    def test_vault_store_right_key(self):
        with MockRequest(self.env):
            vault = self.env["vault"].create({"name": "Vault"})

            self.controller.vault_store_right_keys(None)

            self.controller.vault_store_right_keys({vault.uuid: "new key"})
            self.assertEqual(vault.right_ids.key, "new key")

    @mute_logger("odoo.sql_db")
    def test_vault_inbox_keys(self):
        with MockRequest(self.env):
            self.assertFalse(self.controller.vault_get_inbox())

            inbox = self.inbox.copy({"user_id": self.env.uid})

            response = self.controller.vault_get_inbox()
            self.assertEqual(response, {inbox.token: inbox.key})

    @mute_logger("odoo.sql_db")
    def test_vault_store_inbox_key(self):
        with MockRequest(self.env):
            inbox = self.inbox.copy({"user_id": self.env.uid})
            inbox.user_id = self.env.user

            self.controller.vault_store_inbox(None)

            self.controller.vault_store_inbox({inbox.token: "new key"})
            self.assertEqual(inbox.key, "new key")
