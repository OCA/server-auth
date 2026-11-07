# © 2021 Florian Kantelberg - initOS GmbH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from datetime import datetime
from uuid import uuid4

from odoo.addons.base.tests.common import BaseCommon

_logger = logging.getLogger(__name__)


class TestShare(BaseCommon):
    def test_user_inbox(self):
        user = self.env["res.users"].create(
            {"login": "test", "email": "test@test", "name": "test"}
        )

        user.action_new_inbox_token()

        model = self.env["res.users"]
        token = user.inbox_token

        self.assertEqual(user, model.find_user_of_inbox(token))
        self.assertIn(token, user.inbox_link)

        user.inbox_enabled = False
        self.assertEqual(model, model.find_user_of_inbox(token))

        user.action_new_inbox_token()
        self.assertNotEqual(user.inbox_token, token)

    def test_inbox(self):
        model = self.env["vault.inbox"]
        user = self.env.user
        vals = {
            "name": f"Inbox {user.name}",
            "secret": "secret",
            "iv": "iv",
            "user": user,
            "key": "key",
            "secret_file": "",
            "filename": "",
        }

        # Should create a new inbox for the user
        inbox = model.store_in_inbox(**vals)
        self.assertEqual(inbox.secret, "secret")
        self.assertEqual(inbox.accesses, 0)
        self.assertIn(inbox.token, inbox.inbox_link)

        # No change because of no accesses left
        vals["secret"] = "new secret"
        inbox.store_in_inbox(**vals)
        self.assertEqual(inbox.secret, "secret")
        self.assertEqual(inbox.accesses, 0)

        # Change expected because 5 accesses left
        inbox.accesses = 5
        inbox.store_in_inbox(**vals)
        self.assertEqual(inbox.secret, "new secret")
        self.assertEqual(inbox.accesses, 4)

        # No change because expired
        vals["secret"] = "newer secret"
        inbox.expiration = datetime(1970, 1, 1)
        inbox.store_in_inbox(**vals)
        self.assertEqual(inbox.secret, "new secret")
        self.assertEqual(inbox.accesses, 4)

        # Search for shares
        self.assertEqual(inbox, model.find_inbox(inbox.token))
        self.assertEqual(model, model.find_inbox(uuid4()))

    def test_send_wizard(self):
        user = self.env.user
        wiz = self.env["vault.send.wizard"].create(
            {
                "name": uuid4(),
                "iv": "iv",
                "key_user": "key",
                "key": "k",
                "secret": uuid4(),
                "user_id": user.id,
            }
        )

        # Create a new inbox
        wiz.action_send()
        self.assertTrue(self.env["vault.inbox"].search([("name", "=", wiz.name)]))

    def test_store_wizard(self):
        vault = self.env["vault"].create({"name": "Vault"})

        entry = self.env["vault.entry"].create({"vault_id": vault.id, "name": "Entry"})

        wiz = self.env["vault.store.wizard"].create(
            {
                "vault_id": vault.id,
                "entry_id": entry.id,
                "name": uuid4(),
                "iv": "iv",
                "key": "k",
                "secret": uuid4(),
                "secret_temporary": "temp",
                "model": "vault.field",
            }
        )

        vault.right_ids.write({"key": uuid4()})
        self.assertEqual(wiz.master_key, vault.right_ids.key)

        wiz.action_store()

        self.assertEqual(wiz.name, entry.field_ids.name)
