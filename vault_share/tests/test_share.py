# © 2021 Florian Kantelberg - initOS GmbH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import json
import logging
from uuid import uuid4

from odoo import fields
from odoo.exceptions import AccessError
from odoo.tests import Form, new_test_user
from odoo.tools import mute_logger

from odoo.addons.base.tests.common import BaseCommon
from odoo.addons.http_routing.tests.common import MockRequest

from ..controllers import main

_logger = logging.getLogger(__name__)


class TestShare(BaseCommon):
    # Run the tests with the user creating the test data like in previous versions
    _test_user_groups = ()

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = cls.env.user
        cls.vals = {
            "name": f"Share {cls.user.name}",
            "secret": "secret",
            "salt": "sa17",
            "iv": "1v",
            "pin": "12345",
        }

        cls.share = cls.env["vault.share"].create(cls.vals)

    def test_token_generated_on_create(self):
        # Fallback: a token is minted when none is supplied (e.g. code/RPC)
        share = self.env["vault.share"].create(self.vals)
        self.assertTrue(share.token)
        self.assertIsInstance(share.token, str)
        self.assertEqual(share, share.get(share.token))
        self.assertIn(share.token, share.share_link)

        # A supplied token is kept as-is (e.g. the client-generated one)
        share = self.env["vault.share"].create({**self.vals, "token": "fixed-token"})
        self.assertEqual(share.token, "fixed-token")
        self.assertEqual(share, share.get("fixed-token"))

    def test_share_link_kept_on_save(self):
        # The link shown in the form before saving must remain valid
        # Values are passed like the share button of the vault fields does
        defaults = {f"default_{k}": v for k, v in self.vals.items() if k != "name"}
        with Form(self.env["vault.share"].with_context(**defaults)) as form:
            form.name = self.vals["name"]
            link = form.share_link
        share = form.save()
        self.assertTrue(link)
        self.assertEqual(share.share_link, link)
        self.assertEqual(share, share.get(link.rsplit("/", 1)[-1]))

    @mute_logger("odoo.sql_db")
    def test_share(self):
        self.assertEqual(self.share, self.share.get(self.share.token))
        self.assertIn(self.share.token, self.share.share_link)

        # Nothing should happen
        self.share.clean()
        self.assertEqual(self.share, self.share.get(self.share.token))

        # Deletion because of accesses
        share = self.share.create(self.vals)
        share.accesses = 0
        self.assertEqual(None, share.get(share.token))

        # Deletion because of expiration
        share = self.share.create(self.vals)
        share.expiration = fields.Datetime.to_datetime("1970-01-01")
        self.assertEqual(None, share.get(share.token))

        # Search for invalid token
        self.assertEqual(share.browse(), share.get(uuid4()))

    @mute_logger("odoo.sql_db")
    def test_vault_share(self):
        def return_context(template, context):
            self.assertEqual(template, "vault_share.share")
            return json.dumps(context)

        def load(response):
            return json.loads(response.data)

        with MockRequest(self.env) as request_mock:
            request_mock.render = return_context
            controller = main.Controller()

            response = load(controller.vault_share(""))
            self.assertIn("error", response)

            response = load(controller.vault_share(self.share.token))
            self.assertEqual(response["salt"], self.share.salt)

            self.share.accesses = 0
            response = load(controller.vault_share(self.share.token))
            self.assertIn("error", response)

    def test_share_access_rights(self):
        alice = new_test_user(self.env, login="share_alice", groups="base.group_user")
        bob = new_test_user(self.env, login="share_bob", groups="base.group_user")
        share = self.env["vault.share"].with_user(alice).create(self.vals)
        self.assertEqual(share.user_id, alice)
        self.assertTrue(share.log_ids)

        # Other internal users can't see nor read the share or its log
        Share = self.env["vault.share"].with_user(bob)
        self.assertFalse(Share.search([("id", "=", share.id)]))
        self.assertFalse(
            self.env["vault.share.log"]
            .with_user(bob)
            .search([("share_id", "=", share.id)])
        )
        with self.assertRaises(AccessError):
            Share.browse(share.id).read(["secret"])
        with self.assertRaises(AccessError):
            Share.browse(share.id).unlink()
