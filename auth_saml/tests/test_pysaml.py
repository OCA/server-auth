# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import base64
import html
import os
import os.path as osp
from copy import deepcopy
from unittest.mock import patch

import responses

from odoo.exceptions import AccessDenied, UserError, ValidationError
from odoo.tests import HttpCase, tagged

from .fake_idp import CONFIG, FakeIDP


@tagged("saml", "post_install", "-at_install")
class TestPySaml(HttpCase):
    def setUp(self):
        super().setUp()

        sp_pem_public = None
        sp_pem_private = None

        with open(
            os.path.join(os.path.dirname(__file__), "data", "sp.pem"),
            "r",
            encoding="UTF-8",
        ) as file:
            sp_pem_public = file.read()

        with open(
            os.path.join(os.path.dirname(__file__), "data", "sp.key"),
            "r",
            encoding="UTF-8",
        ) as file:
            sp_pem_private = file.read()

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

        # Create a user with only password, and another with both password and saml id
        self.user, self.user2 = (
            self.env["res.users"]
            .with_context(no_reset_password=True, tracking_disable=True)
            .create(
                [
                    {
                        "name": "User",
                        "email": "test@example.com",
                        "login": "test@example.com",
                        "password": "Lu,ums-7vRU>0i]=YDLa",
                    },
                    {
                        "name": "User with SAML",
                        "email": "user@example.com",
                        "login": "user@example.com",
                        "password": "NesTNSte9340D720te>/-A",
                        "saml_ids": [
                            (
                                0,
                                0,
                                {
                                    "saml_provider_id": self.saml_provider.id,
                                    "saml_uid": "user@example.com",
                                },
                            )
                        ],
                    },
                ]
            )
        )

    def test_ensure_provider_appears_on_login(self):
        # SAML provider should be listed in the login page
        response = self.url_open("/web/login")
        self.assertIn("Login with Authentic", response.text)
        self.assertIn(self.url_saml_request, response.text)

    def test_ensure_provider_appears_on_login_with_redirect_param(self):
        """Test that SAML provider is listed in the login page keeping the redirect"""
        response = self.url_open(
            "/web/login?redirect=%2Fweb%23action%3D37%26model%3Dir.module.module%26view"
            "_type%3Dkanban%26menu_id%3D5"
        )
        self.assertIn("Login with Authentic", response.text)
        self.assertIn(
            "/auth_saml/get_auth_request?pid={}&amp;redirect=%2Fweb%23action%3D37%26mod"
            "el%3Dir.module.module%26view_type%3Dkanban%26menu_id%3D5".format(
                self.saml_provider.id
            ),
            response.text,
        )

    def test_ensure_metadata_present(self):
        response = self.url_open(
            "/auth_saml/metadata?p=%d&d=%s"
            % (self.saml_provider.id, self.env.cr.dbname)
        )

        self.assertTrue(response.ok)
        self.assertTrue("xml" in response.headers.get("Content-Type"))

    def test_ensure_get_auth_request_redirects(self):
        response = self.url_open(
            "/auth_saml/get_auth_request?pid=%d" % self.saml_provider.id,
            allow_redirects=False,
        )
        self.assertTrue(response.ok)
        self.assertEqual(response.status_code, 303)
        self.assertIn(
            "http://localhost:8000/sso/redirect?SAMLRequest=",
            response.headers.get("Location"),
        )

    def test_login_no_saml(self):
        """
        Login with a user account, but without any SAML provider setup
        against the user
        """
        # Standard login using password
        self.authenticate(user="test@example.com", password="Lu,ums-7vRU>0i]=YDLa")
        self.assertEqual(self.session.uid, self.user.id)

        self.logout()

        # Try to log in with a non-existing SAML token
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

    def add_provider_to_user(self):
        """Add a provider to self.user"""
        self.user.write(
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

    def test_login_with_saml(self):
        self.add_provider_to_user()

        redirect_url = self.saml_provider._get_auth_request()
        self.assertIn("http://localhost:8000/sso/redirect?SAMLRequest=", redirect_url)

        response = self.idp.fake_login(redirect_url)
        self.assertEqual(200, response.status_code)
        unpacked_response = response._unpack()

        (database, login, token) = (
            self.env["res.users"]
            .sudo()
            .auth_saml(
                self.saml_provider.id, unpacked_response.get("SAMLResponse"), None
            )
        )

        self.assertEqual(database, self.env.cr.dbname)
        self.assertEqual(login, self.user.login)

        # We should not be able to log in with the wrong token
        with self.assertRaises(AccessDenied):
            self.authenticate(
                user="test@example.com", password="{}-WRONG".format(token)
            )

        # User should now be able to log in with the token
        self.authenticate(user="test@example.com", password=token)

    def test_disallow_user_password_when_changing_ir_config_parameter(self):
        """Test that disabling users from having both a password and SAML ids remove
        users password."""
        # change the option
        self.browse_ref(
            "auth_saml.allow_saml_uid_and_internal_password"
        ).value = "False"
        # The password should be blank and the user should not be able to connect
        with self.assertRaises(AccessDenied):
            self.authenticate(
                user="user@example.com", password="NesTNSte9340D720te>/-A"
            )

    def test_disallow_user_password_new_user(self):
        """Test that a new user can not be set up with both password and SAML ids when
        the disallow option is set."""
        # change the option
        self.browse_ref(
            "auth_saml.allow_saml_uid_and_internal_password"
        ).value = "False"
        with self.assertRaises(UserError):
            self.env["res.users"].with_context(no_reset_password=True).create(
                {
                    "name": "New user with SAML",
                    "email": "user2@example.com",
                    "login": "user2@example.com",
                    "password": "NesTNSte9340D720te>/-A",
                    "saml_ids": [
                        (
                            0,
                            0,
                            {
                                "saml_provider_id": self.saml_provider.id,
                                "saml_uid": "user2",
                            },
                        )
                    ],
                }
            )

    def test_disallow_user_password_no_password_set(self):
        """Test that a new user with SAML ids can not have its password set up when the
        disallow option is set."""
        # change the option
        self.browse_ref(
            "auth_saml.allow_saml_uid_and_internal_password"
        ).value = "False"
        # Create a new user with only SAML ids
        user = (
            self.env["res.users"]
            .with_context(no_reset_password=True, tracking_disable=True)
            .create(
                {
                    "name": "New user with SAML",
                    "email": "user2@example.com",
                    "login": "user2@example.com",
                    "saml_ids": [
                        (
                            0,
                            0,
                            {
                                "saml_provider_id": self.saml_provider.id,
                                "saml_uid": "unused",
                            },
                        )
                    ],
                }
            )
        )
        # Assert that the user password can not be set
        with self.assertRaises(ValidationError):
            user.password = "new password"

    def test_disallow_user_password(self):
        """Test that existing user password is deleted when adding an SAML provider when
        the disallow option is set."""
        # change the option
        self.browse_ref(
            "auth_saml.allow_saml_uid_and_internal_password"
        ).value = "False"
        # Test that existing user password is deleted when adding an SAML provider
        self.authenticate(user="test@example.com", password="Lu,ums-7vRU>0i]=YDLa")
        self.add_provider_to_user()
        with self.assertRaises(AccessDenied):
            self.authenticate(user="test@example.com", password="Lu,ums-7vRU>0i]=YDLa")

    def test_disallow_user_admin_can_have_password(self):
        """Test that admin can have its password set even if the disallow option is set."""
        # change the option
        self.browse_ref(
            "auth_saml.allow_saml_uid_and_internal_password"
        ).value = "False"
        # Test base.user_admin exception
        self.env.ref("base.user_admin").password = "nNRST4j*->sEatNGg._!"

    def test_db_filtering(self):
        # change filter to only allow our db.
        with patch("odoo.http.db_filter", new=lambda *args, **kwargs: []):
            self.add_provider_to_user()

            redirect_url = self.saml_provider._get_auth_request()
            response = self.idp.fake_login(redirect_url)
            unpacked_response = response._unpack()

            for key in unpacked_response:
                unpacked_response[key] = html.unescape(unpacked_response[key])
            response = self.url_open("/auth_saml/signin", data=unpacked_response)
            self.assertFalse(response.ok)
            self.assertIn(response.status_code, [400, 404])

    def test_redirect_after_login(self):
        """Test that providing a redirect will be kept after SAML login."""
        self.add_provider_to_user()

        redirect_url = self.saml_provider._get_auth_request(
            {
                "r": "%2Fweb%23action%3D37%26model%3Dir.module.module%26view_type%3Dkan"
                "ban%26menu_id%3D5"
            }
        )
        response = self.idp.fake_login(redirect_url)
        unpacked_response = response._unpack()

        for key in unpacked_response:
            unpacked_response[key] = html.unescape(unpacked_response[key])
        response = self.url_open(
            "/auth_saml/signin",
            data=unpacked_response,
            allow_redirects=True,
            timeout=300,
        )
        self.assertTrue(response.ok)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.url,
            self.base_url()
            + "/web#action=37&model=ir.module.module&view_type=kanban&menu_id=5",
        )

    def test_disallow_user_password_when_changing_settings(self):
        """Test that disabling the setting will remove passwords from related users"""
        # We activate the settings to allow password login
        self.env["res.config.settings"].create(
            {
                "allow_saml_uid_and_internal_password": True,
            }
        ).execute()

        # Test the user can login with the password
        self.authenticate(user="user@example.com", password="NesTNSte9340D720te>/-A")

        self.env["res.config.settings"].create(
            {
                "allow_saml_uid_and_internal_password": False,
            }
        ).execute()

        with self.assertRaises(AccessDenied):
            self.authenticate(
                user="user@example.com", password="NesTNSte9340D720te>/-A"
            )

    @responses.activate
    def test_download_metadata(self):
        expected_metadata = self.idp.get_metadata()
        responses.add(
            responses.GET,
            "http://localhost:8000/metadata",
            status=200,
            content_type="text/xml",
            body=expected_metadata,
        )
        self.saml_provider.idp_metadata_url = "http://localhost:8000/metadata"
        self.saml_provider.idp_metadata = ""
        self.saml_provider.action_refresh_metadata_from_url()
        self.assertEqual(self.saml_provider.idp_metadata, expected_metadata)

    @responses.activate
    def test_login_with_saml_metadata_empty(self):
        self.saml_provider.idp_metadata_url = "http://localhost:8000/metadata"
        self.saml_provider.idp_metadata = ""
        expected_metadata = self.idp.get_metadata()
        responses.add(
            responses.GET,
            "http://localhost:8000/metadata",
            status=200,
            content_type="text/xml",
            body=expected_metadata,
        )
        self.test_login_with_saml()
        self.assertEqual(self.saml_provider.idp_metadata, expected_metadata)

    @responses.activate
    def test_login_with_saml_metadata_key_changed(self):
        settings = deepcopy(CONFIG)
        settings["key_file"] = osp.join(
            osp.dirname(__file__), "data", "key_idp_expired.pem"
        )
        settings["cert"] = osp.join(
            osp.dirname(__file__), "data", "key_idp_expired.pem"
        )
        expired_idp = FakeIDP(settings=settings)
        self.saml_provider.idp_metadata = expired_idp.get_metadata()
        self.saml_provider.idp_metadata_url = "http://localhost:8000/metadata"
        up_to_date_metadata = self.idp.get_metadata()
        self.assertNotEqual(self.saml_provider.idp_metadata, up_to_date_metadata)
        responses.add(
            responses.GET,
            "http://localhost:8000/metadata",
            status=200,
            content_type="text/xml",
            body=up_to_date_metadata,
        )
        self.test_login_with_saml()
