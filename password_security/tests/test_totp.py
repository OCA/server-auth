# Copyright 2022 Braintec AG
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).


from datetime import datetime, timedelta
from unittest import mock

from passlib.totp import TOTP

from odoo import http
from odoo.tests import HOST, HttpCase, Opener, get_db_name, new_test_user, tagged


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

    def test_totp_expired_password_bounces_to_reset(self):
        """A 2FA login with an expired password lands on a usable reset page

        The second factor is the only path that runs
        PasswordSecurity2FAHome.web_totp, so the test above, which stays at the
        model level, never executes that controller.
        """
        password = "!asdQWE12345_3"
        user = new_test_user(self.env, "tealc", password=password)
        user.partner_id.signup_cancel()

        # Enable the second factor. The secret has to be at least 10 bytes, or
        # passlib emits a PasslibSecurityWarning that Odoo logs through
        # py.warnings and the OCA CI treats as a failure.
        secret = "KRSXG5DFOJTWK3TUKRSXG5DF"
        user.totp_secret = secret
        self.assertTrue(user.totp_enabled)

        # Expire the password so that web_totp() kicks the user out once the
        # second factor succeeds.
        user.password_write_date = datetime.now() - timedelta(days=3)
        self.env["ir.config_parameter"].sudo().set_param(
            "password_security.expiration_days", 1
        )

        self.session = http.root.session_store.new()
        self.opener = Opener(self)
        self.opener.cookies.set("session_id", self.session.sid, domain=HOST, path="/")

        with mock.patch("odoo.http.db_filter") as db_filter:
            db_filter.side_effect = lambda dbs, host=None: [get_db_name()]
            # First factor: the session is left on pre_uid, not logged in yet
            first = self.url_open(
                "/web/login",
                data={
                    "login": "tealc",
                    "password": password,
                    "csrf_token": http.Request.csrf_token(self),
                },
            )
            first.raise_for_status()

            # Second factor
            response = self.url_open(
                "/web/login/totp",
                data={
                    "totp_token": TOTP(key=secret, format="base32").generate().token,
                    "csrf_token": http.Request.csrf_token(self),
                },
            )
        response.raise_for_status()

        # We got kicked out to the reset password page...
        self.assertIn("/web/reset_password", response.request.path_url)
        # ...and the token it was given must actually be usable
        self.assertNotIn("Invalid signup token", response.text)
