# Copyright 2026 Kencove (https://www.kencove.com).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase


class AuthExecuteAsTestCommon(TransactionCase):
    def setUp(self):
        super().setUp()

        self.test_model = self.env["ir.model"].search(
            [("model", "=", "res.partner")], limit=1
        )

        self.whitelist = self.env["auth.api.whitelist"].create(
            {
                "name": "Test Whitelist",
                "description": "Whitelist for testing",
            }
        )

        self.whitelist_line = self.env["auth.api.whitelist.line"].create(
            {
                "whitelist_id": self.whitelist.id,
                "model_id": self.test_model.id,
                "method": "search_read",
                "clean_response": True,
            }
        )

        self.client = self.env["auth.api.client"].create(
            {
                "name": "Test Client",
                "whitelist_id": self.whitelist.id,
            }
        )

        self.test_user = self.env["res.users"].create(
            {
                "name": "Test API User",
                "login": "test_api_user2@example.com",
                "email": "test_api_user2@example.com",
            }
        )
