# Copyright 2025 Alberto Martínez <alberto.martinez@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import time

from odoo.http import _request_stack
from odoo.tests.common import HttpCase
from odoo.tools import DotDict


class TestApiKeyScopeEditable(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.test_user = cls.env["res.users"].create(
            {
                "name": "Tyrion",
                "login": "imp",
                "password": "dracarys123",
                "tz": "Pacific/Chatham",
            }
        )

    def setUp(self):
        def json_data():
            raise ValueError("Expected JSON content is missing")

        super().setUp()
        mock_http = DotDict(
            {
                "httprequest": DotDict(
                    {
                        "environ": {"REMOTE_ADDR": "127.0.0.1"},
                        "cookies": {},
                        "args": {},
                    }
                ),
                "session": {"identity-check-last": time.time()},
                "geoip": {},
                "get_json_data": json_data,
            }
        )
        _request_stack.push(mock_http)
        self.addCleanup(lambda: _request_stack.pop())

    def test_scope_generation(self):
        scoped_env = self.env(user=self.test_user)
        description = scoped_env["res.users.apikeys.description"].create(
            {"name": "API Entry", "scope": "rpc"}
        )
        description.make_key()
        matching_keys = scoped_env["res.users.apikeys"].search([("scope", "=", "rpc")])
        self.assertTrue(matching_keys)

    def test_custom_scope_generation(self):
        scoped_env = self.env(user=self.test_user)
        description = scoped_env["res.users.apikeys.description"].create(
            {
                "name": "API Entry",
                "has_custom_scope": True,
                "custom_scope": "Custom Scope",
            }
        )
        description.make_key()
        matching_keys = scoped_env["res.users.apikeys"].search(
            [("scope", "=", "Custom Scope")]
        )
        self.assertTrue(matching_keys)
