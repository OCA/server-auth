# Copyright 2022 Akretion
# Copyright 2022 Toodigit
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from freezegun import freeze_time

from odoo.exceptions import MissingError
from odoo.tests.common import SavepointCase

from ..common import TooManyVerifResendExc


class TestVerifCodeCase(SavepointCase):
    @classmethod
    @freeze_time("2021-11-01 09:00:00")
    def setUpClass(cls):
        super().setUpClass()
        cls.user = cls.env["res.users"].create(
            {
                "login": "verifuser",
                "name": "Test verif code user",
                "email": "verifuser@test.com",
            }
        )
        cls.user.create_date = "2021-11-01 09:00:00"
        cls.user.generate_verification_code()
        cls.auth_code = cls.user.auth_verification_code_ids

    @classmethod
    @property
    def new_auth_code(cls):
        return cls.user.auth_verification_code_ids - cls.auth_code


class TestVerifCode(TestVerifCodeCase):
    @freeze_time("2021-11-01 09:00:00")
    def test_user_code_generation(self):
        self.assertTrue(self.user.auth_verification_code_ids)
        self.assertTrue(self.auth_code.code_number)
        self.assertTrue(self.auth_code.token)
        # demo data: 3600 minute expiration delay
        self.assertEqual(str(self.auth_code.expiry_date), "2021-11-01 09:05:00")
        self.assertEqual(str(self.auth_code.validity_date), "2021-11-03 21:00:00")
        self.assertFalse(self.auth_code.check_expired())
        self.assertTrue(self.auth_code.check_validity())

    def test_user_code_states(self):
        self.assertEqual(self.user.verification_state, "pending_confirmation")
        self.assertEqual(self.auth_code.state, "pending_confirmation")
        self.auth_code.state = "confirmed"
        self.assertEqual(self.user.verification_state, "confirmed")

    def test_clear_unverified_users(self):
        with freeze_time("2021-11-01 09:00:00"):
            self.env["res.users"].clear_unverified_users(1)
        self.assertTrue(self.user.name)
        with freeze_time("2021-11-11 09:00:00"):
            self.env["res.users"].clear_unverified_users(1)
        with self.assertRaises(MissingError):
            self.assertTrue(self.user.name)

    def test_verification_limit(self):
        for _ in range(5):
            result = self.user.auth_verification_code_ids.verify(000000)
            self.assertEqual(result[0], "Wrong verification code")
        result = self.user.auth_verification_code_ids.verify(000000)
        self.assertEqual(result[0], "Too many verification attempts, try again later")

    def test_code_generation_limit(self):
        for _ in range(4):
            self.user.generate_verification_code()
        with self.assertRaises(TooManyVerifResendExc):
            self.user.generate_verification_code()

    def test_code_send_email(self):
        mails_before = self.env["mail.mail"].search([])
        self.user.generate_verification_code()
        new_mail = self.env["mail.mail"].search([]) - mails_before
        self.assertTrue(new_mail)
        self.assertEqual(new_mail.email_to, "verifuser@test.com")
        self.assertIn(
            str(self.user.last_verif_code.code_number), new_mail.body_html,
        )

    def test_token_code_valid(self):
        token = self.user.get_verification_code_token()
        self.assertEqual(token, self.user.last_verif_code.token)

    @freeze_time("2021-11-01 09:00:00")
    def test_token_code_confirmed(self):
        self.user.last_verif_code.state = "confirmed"
        token = self.user.get_verification_code_token()
        self.assertEqual(token, False)

    @freeze_time("2021-11-01 09:00:00")
    def test_token_code_expired(self):
        self.user.last_verif_code.expiry_date = "2021-11-01 08:00:00"
        self.user.get_verification_code_token()
        self.assertTrue(self.new_auth_code)

    @freeze_time("2021-11-01 09:00:00")
    def test_token_code_invalid(self):
        self.user.last_verif_code.validity_date = "2021-11-01 08:00:00"
        self.user.get_verification_code_token()
        self.assertTrue(self.new_auth_code)
