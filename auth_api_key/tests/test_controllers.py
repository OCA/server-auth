# Copyright 2026 Camptocamp SA (https://www.camptocamp.com).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import json

from odoo.http import Controller, route
from odoo.tests import HttpCase, new_test_user
from odoo.tools import mute_logger


class TestControllers(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.AuthApiKey = cls.env["auth.api.key"]
        cls.test_user = new_test_user(
            cls.env,
            name="Test User",
            login="test",
            password="test",
            email="test@test.com",
            group_ids=[cls.env.ref("base.group_user").id],
            company_id=cls.env.company.id,
        )
        cls.api_key = cls.AuthApiKey.create(
            {"name": "good", "user_id": cls.test_user.id, "key": "api_key"}
        )

        class DummyController(Controller):
            @route("/web/auth-api-key", type="http", auth="api_key", sitemap=False)
            def auth_api_key(self, **params):
                return json.dumps({"name": self.env.user.name})

            @route("/web/auth-api-key-cors", type="http", auth="api_key", cors="*")
            def auth_api_key_cors(self, **params):
                return json.dumps({"name": self.env.user.name})

        cls.env.registry.clear_cache("routing")
        cls.addClassCleanup(cls.env.registry.clear_cache, "routing")

    def test_auth_api_key_ok(self):
        res = self.url_open("/web/auth-api-key", headers={"API-KEY": self.api_key.key})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json(), {"name": self.test_user.name})

    @mute_logger("odoo.addons.base.models.ir_http")
    def test_auth_api_key_wrong(self):
        with self.assertLogs("odoo.http") as cm:
            res = self.url_open("/web/auth-api-key", headers={"API-KEY": "wrong"})
        self.assertEqual(res.status_code, 403)
        self.assertIn("Access Denied", cm.output[0])

    def test_auth_api_key_cors_options(self):
        res = self.url_open("/web/auth-api-key-cors", method="OPTIONS")
        self.assertEqual(res.status_code, 204)
        self.assertEqual(res.headers["Access-Control-Allow-Origin"], "*")
        self.assertIn("API-Key", res.headers["Access-Control-Allow-Headers"])
