# Copyright 2026 Tecnativa - Carlos Roca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
import json

from odoo import fields
from odoo.exceptions import AccessDenied, AccessError, UserError
from odoo.tests import new_test_user
from odoo.tools import mute_logger

from odoo.addons.base.tests.common import BaseCommon
from odoo.addons.http_routing.tests.common import MockRequest

from ..controllers import main


class TestSecurity(BaseCommon):
    _test_user_groups = ()

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.alice = new_test_user(
            cls.env, login="vault_alice", groups="base.group_user"
        )
        cls.bob = new_test_user(cls.env, login="vault_bob", groups="base.group_user")
        cls.manager = new_test_user(
            cls.env, login="vault_manager", groups="base.group_erp_manager"
        )
        for user in (cls.alice, cls.bob):
            cls.env["res.users.key"].with_user(user).store(
                40000, "iv", f"private {user.login}", f"public {user.login}", "salt", 1
            )

        # Vault of Alice shared with Bob without the share permission
        cls.vault = cls.env["vault"].with_user(cls.alice).create({"name": "Shared"})
        cls.right_bob = (
            cls.env["vault.right"]
            .with_user(cls.alice)
            .create({"vault_id": cls.vault.id, "user_id": cls.bob.id})
        )
        cls.right_bob.write(
            {
                "perm_create": False,
                "perm_write": False,
                "perm_share": False,
                "perm_delete": False,
            }
        )
        cls.entry = (
            cls.env["vault.entry"]
            .with_user(cls.alice)
            .create({"vault_id": cls.vault.id, "name": "Entry"})
        )
        cls.controller = main.Controller()

    # S2: actions on other users
    def test_invalidate_key_of_other_user(self):
        right_alice = self.vault.right_ids.filtered(lambda r: r.user_id == self.alice)
        with self.assertRaises(AccessError):
            self.alice.with_user(self.bob).action_invalidate_key()
        self.assertTrue(right_alice.exists())
        self.assertTrue(self.alice.keys.filtered("current"))

    def test_invalidate_own_key(self):
        self.bob.with_user(self.bob).action_invalidate_key()
        self.assertFalse(self.right_bob.exists())

    def test_new_inbox_token_of_other_user(self):
        token = self.alice.inbox_token
        with self.assertRaises(AccessError):
            self.alice.with_user(self.bob).action_new_inbox_token()
        self.assertEqual(self.alice.inbox_token, token)

    def test_new_inbox_token_allowed(self):
        token = self.alice.inbox_token
        self.alice.with_user(self.alice).action_new_inbox_token()
        self.assertNotEqual(self.alice.inbox_token, token)

        token = self.alice.inbox_token
        self.alice.with_user(self.manager).action_new_inbox_token()
        self.assertNotEqual(self.alice.inbox_token, token)

    # S6: inbox token readable by other users
    def test_inbox_token_not_readable_by_others(self):
        with self.assertRaises(AccessError):
            self.alice.with_user(self.bob).read(["inbox_token"])
        self.assertFalse(self.alice.with_user(self.bob).inbox_link)

    def test_inbox_link_readable_by_owner_and_manager(self):
        token = self.alice.inbox_token
        self.assertIn(token, self.alice.with_user(self.alice).inbox_link)
        self.assertIn(token, self.alice.with_user(self.manager).inbox_link)

    # S3: store wizard with arbitrary models
    def test_store_wizard_model(self):
        values = {
            "vault_id": self.vault.id,
            "entry_id": self.entry.id,
            "name": "Secret",
            "iv": "iv",
            "key": "k",
            "secret": "secret",
            "secret_temporary": "temp",
        }
        wizard = (
            self.env["vault.store.wizard"]
            .with_user(self.alice)
            .create(dict(values, model="res.partner"))
        )
        with self.assertRaises(UserError):
            wizard.action_store()

        wizard.model = "vault.field"
        wizard.action_store()
        self.assertEqual(self.entry.field_ids.name, "Secret")

    @mute_logger("odoo.addons.vault.wizards.vault_store_wizard")
    def test_store_wizard_error_is_raised(self):
        # Bob can't create in the vault, the error must be shown to the user
        wizard = (
            self.env["vault.store.wizard"]
            .with_user(self.bob)
            .create(
                {
                    "vault_id": self.vault.id,
                    "entry_id": self.entry.id,
                    "name": "Secret",
                    "iv": "iv",
                    "key": "k",
                    "secret": "secret",
                    "secret_temporary": "temp",
                    "model": "vault.field",
                }
            )
        )
        with self.assertRaises(AccessError):
            wizard.action_store()

    # S4: replace route with arbitrary models
    def test_replace_invalid_model(self):
        partner = self.env["res.partner"].create({"name": "Partner"})
        with MockRequest(self.env(user=self.alice)):
            with self.assertRaises(AccessDenied):
                self.controller.vault_replace(
                    [{"model": "res.partner", "id": partner.id, "name": "Hacked"}]
                )
            with self.assertRaises(AccessDenied):
                self.controller.vault_replace(
                    [{"model": "vault.field", "id": 999999999, "value": "test"}]
                )
        self.assertEqual(partner.name, "Partner")

    # S7: public inbox
    def _inbox_request(self, token, **params):
        def render(template, context):
            return json.dumps(context)

        with MockRequest(self.env) as request_mock:
            request_mock.render = render
            request_mock.httprequest.method = "POST"
            request_mock.params = {
                "name": "Name",
                "encrypted": "secret",
                "iv": "iv",
                "key": "key",
                **params,
            }
            return json.loads(self.controller.vault_inbox(token).data)

    def test_inbox_expired(self):
        inbox = self.env["vault.inbox"].create(
            {
                "user_id": self.alice.id,
                "name": "Inbox",
                "key": "key",
                "iv": "iv",
                "secret": "old",
                "accesses": 5,
                "expiration": fields.Datetime.to_datetime("2000-01-01"),
            }
        )
        response = self._inbox_request(inbox.token)
        self.assertIn("error", response)
        self.assertNotIn("message", response)
        self.assertEqual(inbox.secret, "old")

    def test_inbox_log(self):
        inbox = self.env["vault.inbox"].create(
            {
                "user_id": self.alice.id,
                "name": "Inbox",
                "key": "key",
                "iv": "iv",
                "secret": "old",
                "accesses": 5,
            }
        )
        response = self._inbox_request(inbox.token)
        self.assertIn("message", response)
        self.assertEqual(inbox.secret, "secret")
        self.assertNotIn("False", inbox.log_ids[:1].name)

    def test_inbox_max_size(self):
        self.env["ir.config_parameter"].set_int("vault.inbox_max_size", 10)
        response = self._inbox_request(
            self.alice.inbox_token,
            encrypted="",
            encrypted_file=base64.b64encode(b"x" * 100).decode(),
            filename="file.txt",
        )
        self.assertIn("error", response)
        self.assertFalse(
            self.env["vault.inbox"].search([("user_id", "=", self.alice.id)])
        )

    def test_send_wizard_log(self):
        wizard = (
            self.env["vault.send.wizard"]
            .with_user(self.alice)
            .create(
                {
                    "name": "Sent secret",
                    "iv": "iv",
                    "key_user": "key",
                    "key": "k",
                    "secret": "secret",
                    "user_id": self.bob.id,
                }
            )
        )
        wizard.action_send()
        inbox = self.env["vault.inbox"].search([("name", "=", "Sent secret")])
        self.assertIn(self.alice.name, inbox.log_ids.name)
        self.assertNotIn(self.bob.name, inbox.log_ids.name)
