# Copyright 2021 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import requests

from odoo.tests.common import HOST, PORT, HttpCase


class TestAuthMethod(HttpCase):
    def _assert_no_autologin(self, query=""):
        r = requests.get(
            f"http://{HOST}:{PORT}/web/login{query}", allow_redirects=False
        )
        self.assertNotEqual(r.status_code, 303)
        self.assertTrue(r.ok)

    def _assert_autologin(self, query=""):
        r = requests.get(
            f"http://{HOST}:{PORT}/web/login{query}", allow_redirects=False
        )
        self.assertEqual(r.status_code, 303)

    def test_end_to_end_default_providers(self):
        # by default no provider is configured
        providers = self.env["auth.oauth.provider"].search(
            [("enabled", "=", True), ("autologin", "=", True)]
        )
        self.assertFalse(providers)
        self._assert_no_autologin()

    def test_end_to_end_one_provider(self):
        providers = self.env["auth.oauth.provider"].search(
            [("enabled", "=", True), ("autologin", "=", False)]
        )
        self.assertEqual(len(providers), 1)
        providers.autologin = True
        providers.flush()
        self._assert_autologin()
        self._assert_no_autologin(query="?no_autologin=1")
        self._assert_no_autologin(query="?error=...")
        self._assert_no_autologin(query="?oauth_error=...")
