# Copyright 2023 Onestein (<https://www.onestein.eu>)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from datetime import datetime, timedelta
from unittest import mock

from odoo import http
from odoo.exceptions import UserError, ValidationError
from odoo.modules.registry import Registry
from odoo.tests.common import HOST, HttpCase, Opener, get_db_name, new_test_user, tagged


@tagged("-at_install", "post_install")
class TestPasswordSecurityLogin(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.username = "jackoneill"
        cls.passwd = "!asdQWE12345_3"

        # Create user with strong password: no error raised
        new_test_user(cls.env, cls.username, password=cls.passwd)

    def login(self, username, password):
        """Log in with provided credentials."""
        self.session = http.root.session_store.new()
        self.opener = Opener(self)
        self.opener.cookies.set("session_id", self.session.sid, domain=HOST, path="/")

        with mock.patch("odoo.http.db_filter") as db_filter:
            db_filter.side_effect = lambda dbs, host=None: [get_db_name()]
            res_post = self.url_open(
                "/web/login",
                data={
                    "login": username,
                    "password": password,
                    "csrf_token": http.Request.csrf_token(self),
                },
            )
        res_post.raise_for_status()

        return res_post

    def test_01_create_user_fail(self):
        """It should fail when creating user with short password"""
        # Short password: UserError is raised
        with self.assertRaises(UserError):
            new_test_user(self.env, "new_user", password="abc")

    def test_02_create_user_fail(self):
        """It should fail when creating user with weak password"""
        # Weak password: ValidationError is raised
        with self.assertRaises(ValidationError):
            new_test_user(self.env, "new_user", password="abcdefgh")

    def test_03_web_login_success(self):
        """Allow authenticating by login"""

        # Log in
        response = self.login(self.username, self.passwd)

        # Ensure we end up on the right page
        self.assertEqual(response.request.path_url, "/odoo")
        self.assertEqual(response.status_code, 200)

    def test_04_web_login_fail(self):
        """Fail authenticating with wrong password"""

        # Try to log in
        response = self.login(self.username, "wrong")

        # Ensure we stay on the login page
        self.assertEqual(response.request.path_url, "/web/login")
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            "Wrong login/password",
            response.text,
        )

    def test_05_web_login_expire_pass(self):
        """It should expire password if necessary"""

        # Make password expired
        three_days_ago = datetime.now() - timedelta(days=3)

        with Registry(get_db_name()).cursor() as cr:
            env = self.env(cr)
            user = env["res.users"].search([("login", "=", self.username)])
            user.password_write_date = three_days_ago
            self.env["ir.config_parameter"].sudo().set_param(
                "password_security.expiration_days", 1
            )

        # Try to log in
        response = self.login(self.username, self.passwd)

        # Ensure we end up on the password reset page
        self.assertIn("/web/reset_password", response.request.path_url)

    def test_06_web_login_log_out_if_expired(self):
        """It should log out user if password expired"""

        # Log in
        response = self.login(self.username, self.passwd)

        # Ensure we end up on the right page
        self.assertEqual(response.request.path_url, "/odoo")
        self.assertEqual(response.status_code, 200)

        # Make password expired while still logged in
        three_days_ago = datetime.now() - timedelta(days=3)

        with Registry(get_db_name()).cursor() as cr:
            env = self.env(cr)
            user = env["res.users"].search([("login", "=", self.username)])
            user.password_write_date = three_days_ago
            self.env["ir.config_parameter"].sudo().set_param(
                "password_security.expiration_days", 1
            )

        # Try to access just a page
        req_page1 = self.url_open("/web")
        self.assertEqual(req_page1.request.path_url, "/web")
        self.assertEqual(req_page1.status_code, 200)

        # Try to log in again
        response = self.login(self.username, self.passwd)

        # Ensure we end up on the password reset page
        self.assertIn("/web/reset_password", response.request.path_url)

        # Try to access just a page: user kicked out
        req_page2 = self.url_open("/web")
        self.assertTrue(req_page2.request.path_url.startswith("/web/login"))
        self.assertEqual(req_page2.status_code, 200)

    def test_07_web_login_redirect(self):
        """It should redirect w/ hash to reset after expiration"""

        # Emulate password expired
        with mock.patch(
            "odoo.addons.password_security.models.res_users.ResUsers._password_has_expired"
        ) as func_password_has_expired:
            func_password_has_expired.return_value = True

            # Try to log in
            response = self.login(self.username, self.passwd)

        # Ensure we end up on the password reset page
        self.assertIn("/web/reset_password", response.request.path_url)

        # Try to access just a page: user kicked out
        req_page = self.url_open("/web")
        self.assertTrue(req_page.request.path_url.startswith("/web/login"))
        self.assertEqual(req_page.status_code, 200)

    def test_08_web_login_expire_pass_reset_token_is_valid(self):
        """The expiry bounce should land on a usable reset password page

        Regression test for an "Invalid signup token" error on that page. In
        19.0 res.users._login() is an instance method running on the request
        env. When the user already has a timezone, the browser ``tz`` cookie
        makes ``not user.login_date`` evaluate, which loads login_date (a
        related field on log_ids.create_date) into the env cache *before*
        _update_last_login() creates the new res.users.log. That stale value
        is then signed into the signup token by _generate_signup_token(), and
        validating the token against the fresh login_date rejects it.
        """
        tz = "Europe/Brussels"

        with Registry(get_db_name()).cursor() as cr:
            env = self.env(cr)
            user = env["res.users"].search([("login", "=", self.username)])
            # A timezone must already be set: `not user.tz or not
            # user.login_date` only reaches login_date when user.tz is truthy.
            user.tz = tz
            # Expire the password so that web_login() bounces to the reset page
            user.password_write_date = datetime.now() - timedelta(days=3)
            env["ir.config_parameter"].sudo().set_param(
                "password_security.expiration_days", 1
            )
            # A previous login, backdated so the stale and the fresh
            # login_date really differ: create_date is truncated to the second
            # and both would otherwise collapse into the same value.
            # It is filled from cr.now(), a PostgreSQL NOW() cached for the
            # whole transaction, so freezing the clock with freezegun does not
            # move it, and it cannot be passed in the create values either
            # since LOG_ACCESS_COLUMNS are dropped from them. Patch the cursor
            # clock around the create instead.
            two_days_ago = datetime.now() - timedelta(days=2)
            with mock.patch.object(type(cr), "now", return_value=two_days_ago):
                # sudo() keeps env.uid, so create_uid is still the user,
                # while granting the admin-only create on res.users.log.
                log = env["res.users.log"].with_user(user).sudo().create({})
            self.assertEqual(log.create_uid, user)
            self.assertAlmostEqual(
                log.create_date, two_days_ago, delta=timedelta(minutes=1)
            )

        self.session = http.root.session_store.new()
        self.opener = Opener(self)
        self.opener.cookies.set("session_id", self.session.sid, domain=HOST, path="/")
        # Only a real browser sends this cookie, which is why the rest of the
        # suite never reaches the faulty branch.
        self.opener.cookies.set("tz", tz, domain=HOST, path="/")

        with mock.patch("odoo.http.db_filter") as db_filter:
            db_filter.side_effect = lambda dbs, host=None: [get_db_name()]
            response = self.url_open(
                "/web/login",
                data={
                    "login": self.username,
                    "password": self.passwd,
                    "csrf_token": http.Request.csrf_token(self),
                },
            )
        response.raise_for_status()

        # We got kicked out to the reset password page...
        self.assertIn("/web/reset_password", response.request.path_url)
        # ...and the token it was given must actually be usable
        self.assertNotIn("Invalid signup token", response.text)
