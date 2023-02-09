# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from lxml import html
from werkzeug.test import Client
from werkzeug.wrappers import BaseResponse

from odoo.service import wsgi_server
from odoo.tests import common, tagged


@tagged("post_install", "-at_install")
class TestUI(common.HttpCase):
    """
    This test was carried out in the same way as that the test_ui.py
    in auth_admin_passkey.
    Thanks to Sylvain Le Gal.
    """

    def setUp(self):
        super(TestUI, self).setUp()

        with self.registry.cursor() as test_cursor:
            env = self.env(test_cursor)

            self.ResUsers = self.env["res.users"]
            self.ResPartner = self.env["res.partner"]
            self.user_device_code = "123456789012"
            self.bad_device_code = "345678098765"
            self.partner_user = self.ResPartner.create(
                {
                    "name": "User Device Code",
                    "email": "user.device@example.com",
                }
            )
            self.user = self.ResUsers.create(
                {
                    "name": "User Device Code",
                    "login": "user_device",
                    "email": "device@user.login",
                    "partner_id": self.partner_user.id,
                    "device_code": self.user_device_code,
                    "is_allowed_to_connect_with_device": True,
                }
            )

            self.dbname = env.cr.dbname

        self.werkzeug_environ = {"REMOTE_ADDR": "127.0.0.1"}
        self.test_client = Client(wsgi_server.application, BaseResponse)
        self.test_client.get("/web/session/logout")

    def html_doc(self, response):
        """Get an HTML LXML document."""
        return html.fromstring(response.data)

    def get_request(self, url, data=None):
        return self.test_client.get(url, query_string=data, follow_redirects=True)

    def csrf_token(self, response):
        """Get a valid CSRF token."""
        doc = self.html_doc(response)
        return doc.xpath("//input[@name='csrf_token']")[1].get("value")

    def post_request(self, url, data=None):
        return self.test_client.post(
            url, data=data, follow_redirects=True, environ_base=self.werkzeug_environ
        )

    def test_01_ui_normal_login_succeed(self):
        # Our user wants to go to backoffice part of Odoo
        response = self.get_request("/web/", data={"db": self.dbname})

        # He notices that his redirected to login page as not authenticated
        self.assertIn("oe_login_device_form", response.data.decode("utf8"))

        # He needs to enter his credentials and submit the form
        data = {
            "device_code": self.user.device_code,
            "csrf_token": self.csrf_token(response),
            "db": self.dbname,
        }
        response = self.post_request("/auth_device/login", data=data)

        # He notices that his redirected to backoffice
        self.assertNotIn("oe_login_device_form", response.data.decode("utf8"))

    def test_02_normal_login_fail(self):
        # Our user wants to go to backoffice part of Odoo
        response = self.get_request("/web/", data={"db": self.dbname})

        # He notices that he's redirected to login page as not authenticated
        self.assertIn("oe_login_device_form", response.data.decode("utf8"))

        # He needs to enter his credentials and submit the form
        data = {
            "device_code": self.bad_device_code,
            "csrf_token": self.csrf_token(response),
            "db": self.dbname,
        }
        response = self.post_request("/auth_device/login", data=data)

        # He mistyped his password so he's redirected to login page again
        self.assertIn("oe_login_device_form", response.data.decode("utf8"))

    def test_03_no_login(self):
        # Our user wants to go to backoffice part of Odoo
        response = self.get_request("/web/", data={"db": self.dbname})

        # He notices that he's redirected to login page as not authenticated
        self.assertIn("oe_login_device_form", response.data.decode("utf8"))

        # He forgot to enter his credentials and submit the form
        data = {
            "csrf_token": self.csrf_token(response),
            "db": self.dbname,
        }
        response = self.post_request("/auth_device/login", data=data)

        # He forgot to complete the form so he's redirected to login page again
        self.assertIn("oe_login_device_form", response.data.decode("utf8"))
