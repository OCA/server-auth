# Copyright 2022 Braintec AG
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).


from odoo.tests import HttpCase, tagged


@tagged("post_install", "-at_install")
class TestTOTP(HttpCase):
    def test_totp(self):
        uid = self.env.ref("base.user_demo").id
        self.assertEqual(uid, self.env.ref("base.user_demo").id)

        self.authenticate(user="demo", password="demo")
        self.assertEqual(self.session.uid, uid)

        self.assertEqual(self.env.user._password_has_expired(), False)
        self.assertEqual(self.env.user.partner_id.signup_type, False)
        self.env.user.action_expire_password()
        self.assertEqual(self.env.user.partner_id.signup_type, "reset")

        self.logout()
        self.assertNotEqual(self.session.uid, uid)
