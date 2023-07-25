# Copyright 2016 LasLabs Inc.
# Copyright 2023 Onestein (<https://www.onestein.eu>)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from unittest import mock

from requests.exceptions import HTTPError

from odoo import http
from odoo.exceptions import ValidationError
from odoo.tests.common import HOST, HttpCase, Opener, get_db_name, tagged

from odoo.addons.auth_signup.models.res_users import SignupError


class EndTestException(Exception):
    """It allows for isolation of resources by raise"""


@tagged("-at_install", "post_install")
class TestPasswordSecuritySignup(HttpCase):
    def signup(self, username, password):
        """Signup user"""
        self.session = http.root.session_store.new()
        self.opener = Opener(self.env.cr)
        self.opener.cookies.set("session_id", self.session.sid, domain=HOST, path="/")

        with mock.patch("odoo.http.db_filter") as db_filter:
            db_filter.side_effect = lambda dbs, host=None: [get_db_name()]
            res_post = self.url_open(
                "/web/signup",
                data={
                    "login": username,
                    "name": username,
                    "password": password,
                    "confirm_password": password,
                    "csrf_token": http.Request.csrf_token(self),
                },
            )
        res_post.raise_for_status()

        return res_post

    def test_01_signup_user_fail(self):
        """It should fail when signup user with weak password"""
        # Weak password: signup failed
        response = self.signup("jackoneill", "jackoneill")

        # Ensure we stay in the signup page
        self.assertEqual(response.request.path_url, "/web/signup")
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            "Must contain the following:",
            response.text,
        )

    def test_02_signup_user_success(self):
        """It should succeed when signup user with strong password"""
        # Weak password: signup failed
        response = self.signup("jackoneill", "!asdQWE12345_3")

        # Ensure we were logged in
        self.assertEqual(
            response.request.path_url, "/web/login_successful?account_created=True"
        )
        self.assertEqual(response.status_code, 200)

    def test_03_create_user_signup(self):
        """Password is checked when signup to create a new user"""
        partner = self.env["res.partner"].create({"name": "test partner"})
        vals = {
            "name": "Test User",
            "login": "test_user",
            "email": "test_user@odoo.com",
            "password": "test_user_password",
            "partner_id": partner.id,
        }

        # Weak password: SignupError is raised
        with self.assertRaises(SignupError):
            self.env["res.users"].signup(vals)

        # Stronger password: no error raised
        vals["password"] = "asdQWE12345_3"
        login, pwd = self.env["res.users"].signup(vals)

        # check created user
        created_user = self.env["res.users"].search([("login", "=", "test_user")])
        self.assertEqual(login, "test_user")
        password_write_date = created_user.password_write_date
        self.assertTrue(password_write_date)

        # Weak password: ValidationError is raised
        with self.assertRaises(ValidationError):
            created_user.password = "test_user_password"
        self.assertEqual(password_write_date, created_user.password_write_date)

        # Stronger password: no error raised
        created_user.password = "!asdQWE12345_3"
        self.assertNotEqual(password_write_date, created_user.password_write_date)

    def test_04_web_auth_signup_invalid_qcontext(self):
        """It should catch AttributeError"""

        with mock.patch("odoo.http.db_filter") as db_filter:
            db_filter.side_effect = lambda dbs, host=None: [get_db_name()]
            with self.assertRaises(AttributeError):
                # 'TestPasswordSecuritySignup' object has no attribute 'session'
                self.url_open(
                    "/web/signup",
                    data={
                        "csrf_token": http.Request.csrf_token(self),
                    },
                )

    def test_05_web_auth_signup_invalid_qcontext(self):
        """It should catch EndTestException on signup qcontext"""
        self.session = http.root.session_store.new()
        self.opener = Opener(self.env.cr)
        self.opener.cookies.set("session_id", self.session.sid, domain=HOST, path="/")

        with mock.patch(
            "odoo.addons.auth_signup.controllers.main.AuthSignupHome.get_auth_signup_qcontext"
        ) as qcontext:
            qcontext.side_effect = EndTestException
            with self.assertRaises(HTTPError):
                # Catch HTTPError: 400 Client Error: BAD REQUEST
                self.signup("jackoneill", "!asdQWE12345_3")

    def test_06_web_auth_signup_invalid_render(self):
        """It should render & return signup form on invalid"""
        self.session = http.root.session_store.new()
        self.opener = Opener(self.env.cr)
        self.opener.cookies.set("session_id", self.session.sid, domain=HOST, path="/")

        with mock.patch("odoo.http.db_filter") as db_filter:
            db_filter.side_effect = lambda dbs, host=None: [get_db_name()]
            # Signup: no name or partner given for new user
            response = self.url_open(
                "/web/signup",
                data={
                    "login": "test@test.com",
                    "password": "!asdQWE12345_7",
                    "confirm_password": "!asdQWE12345_7",
                    "csrf_token": http.Request.csrf_token(self),
                },
            )

        # Ensure we stay in the signup page
        self.assertEqual(response.request.path_url, "/web/signup")
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            "Signup: no name or partner given for new user",
            response.text,
        )
        self.assertIn("X-Frame-Options", response.headers)
        self.assertEqual(response.headers["X-Frame-Options"], "SAMEORIGIN")

        self.assertIn("Content-Security-Policy", response.headers)
        self.assertEqual(
            response.headers["Content-Security-Policy"], "frame-ancestors 'self'"
        )
