import base64
import os

from odoo.exceptions import AccessDenied
from odoo.tests import HttpCase, tagged

from .fake_idp import FakeIDP


@tagged("saml", "post_install", "-at_install")
class TestPySaml(HttpCase):
    def setUp(self):
        super().setUp()

        sp_pem_public = None
        sp_pem_private = None

        with open(os.path.join(os.path.dirname(__file__), "data", "sp.pem"), "r") as f:
            sp_pem_public = f.read()

        with open(os.path.join(os.path.dirname(__file__), "data", "sp.key"), "r") as f:
            sp_pem_private = f.read()

        self.saml_provider = self.env["auth.saml.provider"].create(
            {
                "name": "SAML Provider Demo",
                "idp_metadata": FakeIDP().get_metadata(),
                "sp_pem_public": base64.b64encode(sp_pem_public.encode()),
                "sp_pem_private": base64.b64encode(sp_pem_private.encode()),
                "body": "Login with Authentic",
                "active": True,
                "sig_alg": "SIG_RSA_SHA1",
                "matching_attribute": "mail",
            }
        )
        self.url_saml_request = (
            "/auth_saml/get_auth_request?pid=%d" % self.saml_provider.id
        )

        self.idp = FakeIDP([self.saml_provider._metadata_string()])

    def test_ensure_provider_appears_on_login(self):
        # SAML provider should be listed in the login page
        response = self.url_open("/web/login")
        self.assertIn("Login with Authentic", response.text)
        self.assertIn(self.url_saml_request, response.text)

    def test_ensure_metadata_present(self):
        response = self.url_open(
            "/auth_saml/metadata?p=%d&d=%s"
            % (self.saml_provider.id, self.env.cr.dbname)
        )

        self.assertTrue(response.ok)
        self.assertTrue("xml" in response.headers.get("Content-Type"))

    def test_login_no_saml(self):
        """
        Login with a user account, but without any SAML provider setup
        against the user
        """
        # Create an user with only password
        user = (
            self.env["res.users"]
            .with_context(no_reset_password=True)
            .create(
                {
                    "name": "User with Token",
                    "email": "test@example.com",
                    "login": "test@example.com",
                    "password": "Lu,ums-7vRU>0i]=YDLa",
                }
            )
        )

        # Standard login using password
        self.authenticate(user="test@example.com", password="Lu,ums-7vRU>0i]=YDLa")
        self.assertEqual(self.session.uid, user.id)

        self.logout()

        # Try to log-in with an unexisting SAML token
        with self.assertRaises(AccessDenied):
            self.authenticate(user="test@example.com", password="test_saml_token")

        redirect_url = self.saml_provider._get_auth_request()
        self.assertIn("http://localhost:8000/sso/redirect?SAMLRequest=", redirect_url)

        response = self.idp.fake_login(redirect_url)
        self.assertEqual(200, response.status_code)
        unpacked_response = response._unpack()

        with self.assertRaises(AccessDenied):
            self.env["res.users"].sudo().auth_saml(
                self.saml_provider.id, unpacked_response.get("SAMLResponse"), None
            )

    def test_login_with_saml(self):
        user = (
            self.env["res.users"]
            .with_context(no_reset_password=True)
            .create(
                {
                    "name": "User with Token",
                    "email": "test@example.com",
                    "login": "test@example.com",
                    "password": "Lu,ums-7vRU>0i]=YDLa",
                }
            )
        )

        user.write(
            {
                "saml_ids": [
                    (
                        0,
                        0,
                        {
                            "saml_provider_id": self.saml_provider.id,
                            "saml_uid": "test@example.com",
                        },
                    )
                ]
            }
        )

        redirect_url = self.saml_provider._get_auth_request()
        self.assertIn("http://localhost:8000/sso/redirect?SAMLRequest=", redirect_url)

        response = self.idp.fake_login(redirect_url)
        self.assertEqual(200, response.status_code)
        unpacked_response = response._unpack()

        (_database, login, token) = (
            self.env["res.users"]
            .sudo()
            .auth_saml(
                self.saml_provider.id, unpacked_response.get("SAMLResponse"), None
            )
        )

        self.assertEqual(login, user.login)

        # We should not be able to login in the wrong token
        with self.assertRaises(AccessDenied):
            self.authenticate(
                user="test@example.com", password="{}-WRONG".format(token)
            )

        # User should now beable to login with the token
        self.authenticate(user="test@example.com", password=token)
