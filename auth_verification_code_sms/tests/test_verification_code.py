# Copyright 2022 Akretion
# Copyright 2022 Toodigit
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo.addons.auth_verification_code_base.tests.test_verification_code import (
    TestVerifCodeCase,
)


class TestVerifCodeSms(TestVerifCodeCase):
    def test_code_send_sms(self):
        self.user.mobile = "+0123456789"
        sms_before = self.env["sms.sms"].search([])
        self.user.generate_verification_code()
        sms_new = self.env["sms.sms"].search([]) - sms_before
        self.assertEqual(sms_new.number, "+0123456789")
        self.assertIn(
            self.user.auth_verification_code_ids[-1].code_number, sms_new.body
        )
