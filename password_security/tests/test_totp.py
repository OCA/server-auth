# Copyright 2022 Braintec AG
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).


from odoo.tests import HttpCase, tagged
from odoo.tests.common import new_test_user


@tagged("post_install", "-at_install")
class TestTOTP(HttpCase):
    def setUp(self):
        super().setUp()
        self.username = "totp_user"
        self.password = "!asdQWE12345_3"
        self.user = new_test_user(self.env, self.username, password=self.password)

    def test_totp(self):
        # 1. Login with a regular user
        uid = self.user.id
        self.assertEqual(uid, self.user.id)

        # 2. Check that we are logged in
        self.authenticate(user=self.username, password=self.password)
        self.assertEqual(self.session.uid, uid)

        user = self.env["res.users"].browse(uid)

        # 3. Check expired password
        # signup_type has been set to "reset"
        self.assertEqual(user._password_has_expired(), False)
        self.assertEqual(user.partner_id.signup_type, False)
        user.action_expire_password()
        self.assertEqual(user.partner_id.signup_type, "reset")

        self.logout()
        self.assertNotEqual(self.session.uid, uid)
