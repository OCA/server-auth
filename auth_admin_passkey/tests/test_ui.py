# Copyright (C) 2013-Today GRAP (http://www.grap.coop)
# @author Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from lxml import html
from werkzeug.test import Client
from werkzeug.wrappers import Response

from odoo import http
from odoo.tests import common, tagged
from odoo.tools import config


@tagged("post_install", "-at_install")
class TestUI(common.HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.werkzeug_environ = {"REMOTE_ADDR": "127.0.0.1"}
        cls.test_client = Client(http.root, Response)
        cls.test_client.get("/web/session/logout")

    def setUp(self):
        super().setUp()
        with self.registry.cursor() as test_cursor:
            env = self.env(test_cursor)

            self.user_login = "auth_admin_passkey_user"
            self.user_password = "Auth_admin_passkey_password*1"
            self.sysadmin_passkey = "SysAdminPasskeyPa$$w0rd"
            # sysadmin_passkey encrypted with command:
            #   echo -n 'SysAdminPasskeyPa$$w0rd' | sha512sum
            self.sysadmin_passkey_encrypted = (
                "364e3543996125e3408"
                "4b8eca00e328d4acdff9d24126c53624101812f8ed411fd38ecc9"
                "b64807adbf56b02d0315e209a61a193a85003488ca27af573801e65e"
            )
            self.bad_password = "Bad_password*000001"
            self.bad_login = "bad_login"

            self.user = env["res.users"].create(
                {
                    "login": self.user_login,
                    "password": self.user_password,
                    "name": "auth_admin_passkey User",
                }
            )

            self.dbname = env.cr.dbname

    def html_doc(self, response):
        """Get an HTML LXML document."""
        return html.fromstring(response.data)

    def csrf_token(self, response):
        """Get a valid CSRF token."""
        doc = self.html_doc(response)
        return doc.xpath("//input[@name='csrf_token']")[0].get("value")

    def get_request(self, url, data=None):
        return self.test_client.get(url, query_string=data, follow_redirects=True)

    def post_request(self, url, data=None):
        return self.test_client.post(
            url, data=data, follow_redirects=True, environ_base=self.werkzeug_environ
        )

    def test_01_normal_login_succeed(self):
        # Our user wants to go to backoffice part of Odoo
        response = self.get_request("/web/", data={"db": self.dbname})

        # He notices that his redirected to login page as not authenticated
        self.assertIn("oe_login_form", response.data.decode("utf8"))

        # He needs to enters his credentials and submit the form
        data = {
            "login": self.user_login,
            "password": self.user_password,
            "csrf_token": self.csrf_token(response),
            "db": self.dbname,
        }
        response = self.post_request("/web/login/", data=data)

        # He notices that his redirected to backoffice
        self.assertNotIn("oe_login_form", response.data.decode("utf8"))

    def test_02_normal_login_fail(self):
        # Our user wants to go to backoffice part of Odoo
        response = self.get_request("/web/", data={"db": self.dbname})

        # He notices that he's redirected to login page as not authenticated
        self.assertIn("oe_login_form", response.data.decode("utf8"))

        # He needs to enter his credentials and submit the form
        data = {
            "login": self.user_login,
            "password": self.bad_password,
            "csrf_token": self.csrf_token(response),
            "db": self.dbname,
        }
        response = self.post_request("/web/login/", data=data)

        # He mistyped his password so he's redirected to login page again
        self.assertIn("Wrong login/password", response.data.decode("utf8"))

    def test_03_passkey_login_succeed(self):
        # We enable auth_admin_passkey feature
        config["auth_admin_passkey_password"] = self.sysadmin_passkey
        config["auth_admin_passkey_password_sha512_encrypted"] = False

        # Our passkey user wants to go to backoffice part of Odoo
        response = self.get_request("/web/", data={"db": self.dbname})

        # He notices that he's redirected to login page as not authenticated
        self.assertIn("oe_login_form", response.data.decode("utf8"))

        # He needs to enter his credentials and submit the form
        data = {
            "login": self.user_login,
            "password": self.sysadmin_passkey,
            "csrf_token": self.csrf_token(response),
            "db": self.dbname,
        }
        response = self.post_request("/web/login/", data=data)
        print(f"Passkey: {self.sysadmin_passkey}")
        print("response data")
        print(response)

        # He notices that his redirected to backoffice
        self.assertNotIn("oe_login_form", response.data.decode("utf8"))

    def test_04_passkey_login_fail(self):
        # We disable auth_admin_passkey feature
        config["auth_admin_passkey_password"] = False
        config["auth_admin_passkey_password_sha512_encrypted"] = False

        # Our passkey user wants to go to backoffice part of Odoo
        response = self.get_request("/web/", data={"db": self.dbname})

        # He notices that he's redirected to login page as not authenticated
        self.assertIn("oe_login_form", response.data.decode("utf8"))

        # He needs to enter his credentials and submit the form
        data = {
            "login": self.user_login,
            "password": self.sysadmin_passkey,
            "csrf_token": self.csrf_token(response),
            "db": self.dbname,
        }
        response = self.post_request("/web/login/", data=data)

        # Passkey feature is disabled so he's redirected to login page again
        self.assertIn("Wrong login/password", response.data.decode("utf8"))

    def test_05_passkey_login_encrypted_succeed(self):
        # We enable auth_admin_passkey feature with encryption
        config["auth_admin_passkey_password"] = self.sysadmin_passkey_encrypted
        config["auth_admin_passkey_password_sha512_encrypted"] = True

        # Our passkey user wants to go to backoffice part of Odoo
        response = self.get_request("/web/", data={"db": self.dbname})

        # He notices that he's redirected to login page as not authenticated
        self.assertIn("oe_login_form", response.data.decode("utf8"))

        # He needs to enter his credentials and submit the form
        data = {
            "login": self.user_login,
            "password": self.sysadmin_passkey,
            "csrf_token": self.csrf_token(response),
            "db": self.dbname,
        }
        response = self.post_request("/web/login/", data=data)
        print(f"PasskeyEncrypt: {self.sysadmin_passkey}")
        print("response data")
        print(response)

        # He notices that his redirected to backoffice
        self.assertNotIn("oe_login_form", response.data.decode("utf8"))
