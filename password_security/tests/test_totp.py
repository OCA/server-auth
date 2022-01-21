# Copyright 2022 Braintec AG
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from datetime import datetime, timedelta

from odoo.tests import HttpCase, tagged


@tagged("post_install", "-at_install")
class TestTOTP(HttpCase):
    def test_totp(self):
        # 1. Login with demo user
        uid = self.env.ref("base.user_demo").id
        self.assertEqual(uid, self.env.ref("base.user_demo").id)

        # 2. Check that we are logged in
        self.authenticate(user="demo", password="demo")
        self.assertEqual(self.session.uid, uid)

        # 3. Check expired password
        self.assertEqual(self.env.user._password_has_expired(), False)
        self.env.user.action_expire_password()
        date_tomorrow = datetime.now() + timedelta(days=1)
        self.assertEqual(
            self.env.user.partner_id.signup_expiration.strftime("%m/%d/%Y %H:%M:%S"),
            date_tomorrow.strftime("%m/%d/%Y %H:%M:%S"),
        )

        self.logout()
        self.assertNotEqual(self.session.uid, uid)
