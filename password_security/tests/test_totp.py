# Copyright 2022 Braintec AG
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).


from odoo.tests import HttpCase, new_test_user, tagged


@tagged("post_install", "-at_install")
class TestTOTP(HttpCase):
    def test_totp(self):
        # 1. Provide our own user: demo data is not loaded on the OCA CI, so
        #    base.user_demo cannot be relied upon. The password must satisfy
        #    the policy this very module enforces.
        password = "!asdQWE12345_3"
        user = new_test_user(self.env, "jackoneill", password=password)
        # auth_signup flags a brand new user for signup; base.user_demo was
        # not flagged, so clear it to assert on the password expiry alone.
        user.partner_id.signup_cancel()

        # 2. Check that we are logged in
        self.authenticate(user="jackoneill", password=password)
        self.assertEqual(self.session.uid, user.id)

        # 3. Check expired password
        # signup_type has been set to "reset"
        self.assertEqual(user._password_has_expired(), False)
        self.assertEqual(user.partner_id.signup_type, False)
        user.action_expire_password()
        self.assertEqual(user.partner_id.signup_type, "reset")

        self.logout()
        self.assertNotEqual(self.session.uid, user.id)
