# © 2021 Florian Kantelberg - initOS GmbH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo.tests import TransactionCase

_logger = logging.getLogger(__name__)


class TestShare(TransactionCase):
    def test_user_inbox(self):
        user = self.env["res.users"].create(
            {"login": "test", "email": "test@test", "name": "test"}
        )

        user.action_new_share_token()

        model = self.env["res.users"]
        token = user.inbox_token

        self.assertEqual(user, model.find_user_of_inbox(token))
        self.assertIn(token, user.inbox_link)

        user.inbox_enabled = False
        self.assertEqual(model, model.find_user_of_inbox(token))

        user.action_new_share_token()
        self.assertNotEqual(user.inbox_token, token)
