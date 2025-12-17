# © 2021 Florian Kantelberg - initOS GmbH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import json
import logging
from datetime import datetime
from uuid import uuid4

from odoo.tools import mute_logger

from odoo.addons.base.tests.common import BaseCommon
from odoo.addons.website.tools import MockRequest

from ..controllers import main

_logger = logging.getLogger(__name__)


class TestShare(BaseCommon):
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
        share.expiration = datetime(1970, 1, 1)
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
