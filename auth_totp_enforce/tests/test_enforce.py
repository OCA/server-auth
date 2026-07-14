# Copyright 2026 ForgeFlow S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
import time

from odoo.tests import TransactionCase, new_test_user, tagged

from odoo.addons.auth_totp.models.totp import TIMESTEP, hotp


@tagged("post_install", "-at_install")
class TestEnforce(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.internal_user = new_test_user(
            cls.env,
            login="totp_internal",
            password="totp_internal_pwd",
        )

    def _valid_code(self, secret):
        key = base64.b32decode(secret.replace(" ", "").upper())
        return hotp(key, int(time.time() / TIMESTEP))

    def test_setup_with_valid_code_enables_totp(self):
        secret = self.internal_user._generate_totp_setup_secret()
        self.assertFalse(self.internal_user.totp_enabled)
        code = self._valid_code(secret)
        enforce = self.internal_user.sudo()._totp_enforce_setup(secret, code)
        self.assertTrue(enforce)
        self.assertTrue(self.internal_user.totp_enabled)

    def test_setup_with_wrong_code_is_rejected(self):
        secret = self.internal_user._generate_totp_setup_secret()
        # A code from a far-away time window is outside the match window
        key = base64.b32decode(secret.replace(" ", "").upper())
        wrong_code = hotp(key, int(time.time() / TIMESTEP) - 10000)
        enforce = self.internal_user.sudo()._totp_enforce_setup(secret, wrong_code)
        self.assertFalse(enforce)
        self.assertFalse(self.internal_user.totp_enabled)

    def test_setup_with_non_numeric_code_is_rejected(self):
        secret = self.internal_user._generate_totp_setup_secret()
        enforce = self.internal_user.sudo()._totp_enforce_setup(secret, "not-a-code")
        self.assertFalse(enforce)
        self.assertFalse(self.internal_user.totp_enabled)

    def test_generated_secret_is_valid_base32(self):
        secret = self.internal_user._generate_totp_setup_secret()
        # Must decode without error and yield the expected key size
        key = base64.b32decode(secret.replace(" ", "").upper())
        self.assertEqual(len(key) * 8, 160)
