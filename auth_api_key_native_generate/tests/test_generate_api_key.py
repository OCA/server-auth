# Copyright 2026 Trobz
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import json
from datetime import datetime, timezone
from unittest.mock import patch

from odoo import fields
from odoo.tests import HttpCase, new_test_user, tagged
from odoo.tools import mute_logger

ENDPOINT = "/api/auth/generate_api_key"


@tagged("-at_install", "post_install")
class TestGenerateApiKey(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.password = "Str0ng-P@ssw0rd"
        cls.user = new_test_user(
            cls.env,
            login="api-key-user",
            password=cls.password,
            group_ids=[cls.env.ref("base.group_user").id],
        )

    def _generate(self, payload, *, expected_code=200):
        res = self.url_open(
            ENDPOINT,
            data=json.dumps(payload),
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(res.status_code, expected_code)
        return res

    def _credentials(self, **overrides):
        payload = {
            "db": self.env.cr.dbname,
            "login": "api-key-user",
            "password": self.password,
        }
        payload.update(overrides)
        return payload

    def _parse_expiration(self, body):
        """Parse the ISO 8601 expiration date and check it is UTC-aware."""
        expiration = datetime.fromisoformat(body["expiration_date"])
        self.assertEqual(expiration.utcoffset(), timezone.utc.utcoffset(None))
        return expiration.replace(tzinfo=None)

    def test_generate_ok(self):
        # Clear the parameter so the code default (90 days) is exercised,
        # independently of any value persisted in the database.
        self.env["ir.config_parameter"].set_param(
            "auth_api_key_native_generate.duration", False
        )
        body = self._generate(self._credentials()).json()

        # The returned key must authenticate as the target user with rpc scope.
        uid = self.env["res.users.apikeys"]._check_credentials(
            scope="rpc", key=body["api_key"]
        )
        self.assertEqual(uid, self.user.id)

        # Default validity window is 90 days ahead (UTC).
        expiration = self._parse_expiration(body)
        delta_days = (expiration - fields.Datetime.now()).days
        self.assertGreaterEqual(delta_days, 88)
        self.assertLessEqual(delta_days, 90)

    def test_generate_respects_configured_duration(self):
        self.env["ir.config_parameter"].set_param(
            "auth_api_key_native_generate.duration", "30"
        )
        body = self._generate(self._credentials()).json()
        expiration = self._parse_expiration(body)
        delta_days = (expiration - fields.Datetime.now()).days
        self.assertGreaterEqual(delta_days, 28)
        self.assertLessEqual(delta_days, 30)

    @mute_logger("odoo.addons.base.models.res_users", "odoo.http")
    def test_generate_wrong_password(self):
        self._generate(self._credentials(password="wrong"), expected_code=401)

    def test_generate_missing_fields(self):
        self._generate(
            {"db": self.env.cr.dbname, "login": "api-key-user"}, expected_code=400
        )

    def test_generate_non_object_body(self):
        # Valid JSON that is not an object must be rejected, not 500.
        self._generate([1, 2, 3], expected_code=400)

    def test_generate_oversized_body(self):
        # Body above the route max_content_length must be rejected (413).
        res = self.url_open(
            ENDPOINT,
            data=json.dumps({"db": self.env.cr.dbname, "pad": "x" * 9000}),
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(res.status_code, 413)

    @mute_logger("odoo.http")
    def test_generate_unknown_db(self):
        self._generate(
            self._credentials(db="this-db-does-not-exist"), expected_code=404
        )

    def test_generate_refused_when_mfa_enabled(self):
        # A user with two-factor authentication must not obtain a key by
        # password alone. _mfa_url() is truthy when MFA is enabled.
        users_cls = type(self.env["res.users"])
        with patch.object(users_cls, "_mfa_url", return_value="/web/login/totp"):
            self._generate(self._credentials(), expected_code=403)
