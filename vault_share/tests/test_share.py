# © 2021 Florian Kantelberg - initOS GmbH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from datetime import datetime
from uuid import uuid4

from odoo.tests import TransactionCase

_logger = logging.getLogger(__name__)


class TestShare(TransactionCase):
    def test_share(self):
        user = self.env.user
        model = self.env["vault.share"]
        vals = {
            "name": f"Share {user.name}",
            "secret": "secret",
            "salt": "sa17",
            "iv": "1v",
            "pin": "12345",
        }

        share = model.create(vals)
        self.assertEqual(share, model.get(share.token))
        self.assertIn(share.token, share.share_link)

        # Nothing should happen
        model.clean()
        self.assertEqual(share, model.get(share.token))

        # Deletion because of accesses
        share = model.create(vals)
        share.accesses = 0
        self.assertEqual(None, model.get(share.token))

        # Deletion because of expiration
        share = model.create(vals)
        share.expiration = datetime(1970, 1, 1)
        self.assertEqual(None, model.get(share.token))

        # Search for invalid token
        self.assertEqual(model, model.get(uuid4()))
