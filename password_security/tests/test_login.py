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
    def setUp(self):
        super().setUp()
        self.username = "jackoneill"
        self.passwd = "!asdQWE12345_3"

        new_test_user(self.env, self.username, password=self.passwd)

    def login(self, username, password):
        """Authentification avec les identifiants fournis."""
        self.session = http.root.session_store.new()
        # Odoo 19 : Opener prend l'instance HttpCase, pas un cursor
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
        """Doit échouer lors de la création avec un mot de passe trop court."""
        with self.assertRaises(UserError):
            new_test_user(self.env, "new_user", password="abc")

    def test_02_create_user_fail(self):
        """Doit échouer lors de la création avec un mot de passe faible."""
        with self.assertRaises(ValidationError):
            new_test_user(self.env, "new_user", password="abcdefgh")

    def test_03_web_login_success(self):
        """Doit permettre l'authentification."""
        response = self.login(self.username, self.passwd)
        self.assertEqual(response.request.path_url, "/odoo")
        self.assertEqual(response.status_code, 200)

    def test_04_web_login_fail(self):
        """Doit échouer avec un mauvais mot de passe."""
        response = self.login(self.username, "wrong")
        self.assertEqual(response.request.path_url, "/web/login")
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            "Wrong login/password",
            response.text,
        )

    def test_05_web_login_expire_pass(self):
        """Doit expirer le mot de passe si nécessaire."""
        three_days_ago = datetime.now() - timedelta(days=3)

        with Registry(get_db_name()).cursor() as cr:
            env = self.env(cr)
            user = env["res.users"].search([("login", "=", self.username)])
            user.password_write_date = three_days_ago
            self.env["ir.config_parameter"].sudo().set_param(
                "password_security.expiration_days", 1
            )

        response = self.login(self.username, self.passwd)
        self.assertIn("/web/reset_password", response.request.path_url)

    def test_06_web_login_log_out_if_expired(self):
        """Doit déconnecter l'utilisateur si le mot de passe a expiré."""
        response = self.login(self.username, self.passwd)
        self.assertEqual(response.request.path_url, "/odoo")
        self.assertEqual(response.status_code, 200)

        three_days_ago = datetime.now() - timedelta(days=3)

        with Registry(get_db_name()).cursor() as cr:
            env = self.env(cr)
            user = env["res.users"].search([("login", "=", self.username)])
            user.password_write_date = three_days_ago
            self.env["ir.config_parameter"].sudo().set_param(
                "password_security.expiration_days", 1
            )

        response = self.login(self.username, self.passwd)
        self.assertIn("/web/reset_password", response.request.path_url)
