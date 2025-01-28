# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import base64
import html
import os
import os.path as osp
import urllib
from copy import deepcopy
from unittest.mock import patch

import responses
from saml2.sigver import SignatureError

from odoo.exceptions import AccessDenied, UserError, ValidationError
from odoo.tests import HttpCase, tagged
from odoo.tools import mute_logger

from odoo.addons.auth_saml.controllers.main import fragment_to_query_string

from .fake_idp import CONFIG, DummyResponse, FakeIDP, UnsignedFakeIDP


@tagged("saml", "post_install", "-at_install")
class TestPySaml(HttpCase):
    def setUp(self):
        super().setUp()

        with open(
            os.path.join(os.path.dirname(__file__), "data", "sp.pem"),
            encoding="UTF-8",
        ) as file:
            sp_pem_public = file.read()

        with open(
            os.path.join(os.path.dirname(__file__), "data", "sp.key"),
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

        # Define a sample function to test the decorator
        def dummy_function(self, **kw):
            return "Function executed"

        # Apply the decorator to the dummy function
        self.decorated_function = fragment_to_query_string(dummy_function)

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
            f"/auth_saml/get_auth_request?pid={self.saml_provider.id}&amp;redirect=%2Fweb%23action%3D37%26mod"
            "el%3Dir.module.module%26view_type%3Dkanban%26menu_id%3D5",
            response.text,
        )

    def test__onchange_name(self):
        temp = self.saml_provider.body
        self.saml_provider.body = ""
        r = self.saml_provider._onchange_name()
        self.assertEqual(r, None)
        self.assertEqual(self.saml_provider.body, self.saml_provider.name)
        self.saml_provider.body = temp

    def test__compute_sp_metadata_url__new_provider(self):
        # Create a new unsaved record
        new_provider = self.env["auth.saml.provider"].new(
            {"name": "New SAML Provider", "sp_baseurl": "http://example.com"}
        )
        # Compute the metadata URL
        new_provider._compute_sp_metadata_url()
        # Assert that sp_metadata_url is False for the new record
        self.assertFalse(new_provider.sp_metadata_url)
        new_provider.unlink()

    def test__compute_sp_metadata_url__provider_has_sp_baseurl(self):
        # Create a new saved record with sp_baseurl set
        temp = self.saml_provider.sp_baseurl
        self.saml_provider.sp_baseurl = "http://example.com"
        self.saml_provider._compute_sp_metadata_url()
        expected_qs = urllib.parse.urlencode(
            {"p": self.saml_provider.id, "d": self.env.cr.dbname}
        )
        expected_url = urllib.parse.urljoin(
            "http://example.com", (f"/auth_saml/metadata?{expected_qs}")
        )
        # Assert that sp_metadata_url is set correctly
        self.assertEqual(self.saml_provider.sp_metadata_url, expected_url)
        self.saml_provider.sp_baseurl = temp

    def _add_mapping_to_provider(self):
        """Add mapping to the provider"""
        self.saml_provider.attribute_mapping_ids = [
            (0, 0, {"attribute_name": "mail", "field_name": "login"}),
            (0, 0, {"attribute_name": "givenName", "field_name": "name"}),
            (
                0,
                0,
                {"attribute_name": "nick_name", "field_name": "name"},
            ),  # This attribute is not in attrs
        ]

    def test__hook_validate_auth_response(self):
        # Create a fake response with attributes
        fake_response = DummyResponse(200, "fake_data")
        fake_response.set_identity(
            {"mail": "new_user@example.com", "givenName": "New", "last_name": "User"}
        )
        self._add_mapping_to_provider()
        # Call the method
        result = self.saml_provider._hook_validate_auth_response(
            fake_response, "test@example.com"
        )

        # Check the result
        self.assertIn("mapped_attrs", result)
        self.assertEqual(result["mapped_attrs"]["login"], "new_user@example.com")
        self.assertEqual(result["mapped_attrs"]["name"], "New")
        self.assertNotIn("middle_name", result["mapped_attrs"])

    def test_get_config_for_provider(self):
        temp = self.saml_provider.sp_baseurl
        self.saml_provider.sp_baseurl = "http://example.com"
        self.saml_provider._get_config_for_provider(None)
        self.saml_provider.sp_baseurl = temp

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
            self.user._check_credentials(
                {"type": "password", "password": "test_saml_token"},
                {"interactive": True},
            )

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
            self.user._check_credentials(
                {"type": "password", "password": "WRONG_TOKEN"},
                {"interactive": True},
            )

        # User should now be able to log in with the token
        self.authenticate(user="test@example.com", password=token)

    def test_login_with_saml_mapping_attributes(self):
        """Test login with SAML on a provider with mapping attributes"""
        self.assertEqual(self.user.name, "User")
        self.assertEqual(self.user.login, "test@example.com")
        self._add_mapping_to_provider()
        self.test_login_with_saml()
        # Changed due to mapping and FakeIDP returning another value
        self.assertEqual(self.user.name, "Test")
        # Not changed
        self.assertEqual(self.user.login, "test@example.com")

    def test_disallow_user_password_when_changing_ir_config_parameter(self):
        """Test that disabling users from having both a password and SAML ids remove
        users password."""
        # change the option
        self.browse_ref(
            "auth_saml.allow_saml_uid_and_internal_password"
        ).value = "False"
        # The password should be blank and the user should not be able to connect
        with self.assertRaises(AccessDenied):
            self.user._check_credentials(
                {"type": "password", "password": "NesTNSte9340D720te>/-A"},
                {"interactive": True},
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

    def test_disallow_user_password_on_option_disable(self):
        """Test that existing user password is deleted when adding an SAML provider when
        the disallow option is set."""
        self.authenticate(user="test@example.com", password="Lu,ums-7vRU>0i]=YDLa")
        # change the option
        self.browse_ref(
            "auth_saml.allow_saml_uid_and_internal_password"
        ).value = "False"
        with self.assertRaises(AccessDenied):
            self.user._check_credentials(
                {"type": "password", "password": "Lu,ums-7vRU>0i]=YDLa"},
                {"interactive": True},
            )

    def test_disallow_user_admin_can_have_password(self):
        """Test that admin can have its password set
        even if the disallow option is set."""
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
            self.user._check_credentials(
                {"type": "password", "password": "NesTNSte9340D720te>/-A"},
                {"interactive": True},
            )

    def test_fragment_to_query_string_no_kw(self):
        """Test the case where no keyword arguments are passed."""
        response = self.decorated_function(self)
        expected_html = """<html><head><script>
                var l = window.location;
                var q = l.hash.substring(1);
                var r = '/' + l.search;
                if(q.length !== 0) {
                    var s = l.search ? (l.search === '?' ? '' : '&') : '?';
                    r = l.pathname + l.search + s + q;
                }
                window.location = r;
            </script></head><body></body></html>"""
        self.assertEqual(response.strip(), expected_html.strip())

    def test_fragment_to_query_string_with_kw(self):
        """Test the case where keyword arguments are passed."""
        response = self.decorated_function(self, key="value")
        self.assertEqual(response, "Function executed")

    def test_sig_alg_selection(self):
        """Test that _sig_alg_selection is returning correct selection."""
        expected_selection = [
            ("SIG_RSA_SHA1", "SIG_RSA_SHA1"),
            ("SIG_RSA_SHA224", "SIG_RSA_SHA224"),
            ("SIG_RSA_SHA256", "SIG_RSA_SHA256"),
            ("SIG_RSA_SHA384", "SIG_RSA_SHA384"),
            ("SIG_RSA_SHA512", "SIG_RSA_SHA512"),
        ]
        self.assertEqual(self.saml_provider._sig_alg_selection(), expected_selection)

    def test_saml_metadata_invalid_provider(self):
        """Accessing SAML metadata with an invalid provider ID should return 404."""
        response = self.url_open(f"/auth_saml/metadata?p=999999&d={self.env.cr.dbname}")
        self.assertEqual(response.status_code, 404)
        self.assertIn("Unknown provider", response.text)

    def test_saml_metadata_missing_parameters(self):
        """Accessing the SAML metadata endpoint without params should return 404."""
        response = self.url_open("/auth_saml/metadata")
        self.assertEqual(response.status_code, 404)
        self.assertIn("Missing parameters", response.text)

    def test_saml_provider_deactivation(self):
        """A deactivated SAML provider should not be usable for authentication."""
        self.saml_provider.active = False

        redirect_url = self.saml_provider._get_auth_request()
        response = self.idp.fake_login(redirect_url)
        unpacked_response = response._unpack()

        with self.assertRaises(AccessDenied):
            self.env["res.users"].sudo().auth_saml(
                self.saml_provider.id, unpacked_response.get("SAMLResponse"), None
            )

    def test_compute_sp_metadata_url_for_new_record(self):
        """Test that sp_metadata_url is set to False for a new (unsaved) provider."""
        new_provider = self.env["auth.saml.provider"].new(
            {"name": "New SAML Provider", "sp_baseurl": "http://example.com"}
        )
        new_provider._compute_sp_metadata_url()
        self.assertFalse(new_provider.sp_metadata_url)

    def test_store_outstanding_request(self):
        """Test that the SAML request ID is stored in the auth_saml.request model."""
        reqid = "test-request-id"
        self.saml_provider._store_outstanding_request(reqid)

        request = self.env["auth_saml.request"].search(
            [("saml_request_id", "=", reqid)]
        )
        self.assertTrue(request)
        self.assertEqual(request.saml_provider_id.id, self.saml_provider.id)

    def test_get_auth_request_redirect_url(self):
        """Test that _get_auth_request returns a valid redirect URL."""
        redirect_url = self.saml_provider._get_auth_request()
        self.assertIsNotNone(redirect_url)
        self.assertIn("SAMLRequest=", redirect_url)

    def test_get_auth_request_valid_provider(self):
        """Test that get_auth_request returns a redirect for a valid provider."""
        response = self.url_open(
            f"/auth_saml/get_auth_request?pid={self.saml_provider.id}",
            allow_redirects=False,
        )
        self.assertEqual(response.status_code, 303)
        self.assertIn("Location", response.headers)
        self.assertIn("SAMLRequest=", response.headers["Location"])

    def test_create_res_users_saml(self):
        """Test that creating a SAML mapping removes the password when disallowed."""
        user = self.env["res.users"].create(
            {
                "name": "Test User",
                "login": "testuser@example.com",
                "password": "securepassword",
            }
        )
        self.env["ir.config_parameter"].set_param(
            "auth_saml.allow_saml_uid_and_internal_password", "False"
        )
        self.env["res.users.saml"].create(
            {
                "user_id": user.id,
                "saml_provider_id": self.env["auth.saml.provider"]
                .create(
                    {
                        "name": "Demo Provider",
                        "sig_alg": "SIG_RSA_SHA1",
                        "idp_metadata": "fake_metadata",
                        "sp_pem_public": base64.b64encode(b"public_key"),
                        "sp_pem_private": base64.b64encode(b"private_key"),
                    }
                )
                .id,
                "saml_uid": "testuser@example.com",
            }
        )
        self.assertFalse(user.password)

    def test_missing_parameters_in_metadata(self):
        """Test that missing parameters in the SAML metadata request return a 404."""
        response = self.url_open("/auth_saml/metadata")
        self.assertEqual(response.status_code, 404)
        self.assertIn("Missing parameters", response.text)

    def test_saml_request_creation(self):
        """Test that a SAML request is correctly stored in the model."""
        self.env["auth_saml.request"].create(
            {
                "saml_provider_id": self.saml_provider.id,
                "saml_request_id": "test-request-id",
            }
        )
        request = self.env["auth_saml.request"].search(
            [("saml_request_id", "=", "test-request-id")]
        )
        self.assertTrue(request)
        self.assertEqual(request.saml_provider_id.id, self.saml_provider.id)

    def test_get_cert_key_path_tempfile(self):
        """Test _get_cert_key_path for non-file storage locations."""
        # Create a mock attachment with base64-encoded data
        self.env["ir.attachment"].create(
            {
                "name": "test.pem",
                "datas": base64.b64encode(b"dummy_cert_key_content").decode("utf-8"),
                "res_model": "auth.saml.provider",
                "res_field": "sp_pem_public",
                "res_id": 1,
            }
        )
        # Mock the _storage method to return a non-file location
        with patch(
            "odoo.addons.base.models.ir_attachment.IrAttachment._storage",
            return_value="db",
        ):
            provider = self.env["auth.saml.provider"].browse(1)
            cert_key_path = provider._get_cert_key_path("sp_pem_public")

            # Verify the temporary file was created and contains the expected content
            with open(cert_key_path, "rb") as f:
                content = f.read()
                self.assertEqual(content, b"dummy_cert_key_content")

            # Clean up the temporary file
            os.remove(cert_key_path)

    def test_signin_no_relaystate_redirect(self):
        """Test redirect to /?type=signup when RelayState is missing."""
        self.add_provider_to_user()

        redirect_url = self.saml_provider._get_auth_request()
        self.assertIn("http://localhost:8000/sso/redirect?SAMLRequest=", redirect_url)

        # Simulate the login request and remove RelayState from the response
        response = self.idp.fake_login(redirect_url)
        response.text = response.text.replace('name="RelayState" value="', "")

        signin_response = self.url_open(
            "/auth_saml/signin",
            data={"SAMLResponse": response.text},
            allow_redirects=False,
        )
        self.assertEqual(signin_response.status_code, 303)
        self.assertIn("/?type=signup", signin_response.headers["Location"])

    def test_signin_redirect_mfa(self):
        """Test redirect to mfa url"""
        self.add_provider_to_user()

        redirect_url = self.saml_provider._get_auth_request({"a": "action"})
        response = self.idp.fake_login(redirect_url)
        unpacked_response = response._unpack()

        for key in unpacked_response:
            unpacked_response[key] = html.unescape(unpacked_response[key])
        with patch.object(
            self.env.registry["res.users"], "_mfa_url", return_value="/web/login/totp"
        ):
            response = self.url_open(
                "/auth_saml/signin",
                data=unpacked_response,
                allow_redirects=True,
                timeout=300,
            )
        self.assertTrue(response.ok)
        self.assertEqual(
            response.url,
            self.base_url() + "/web/login/totp?redirect=%2F%23action%3Daction",
        )

    def test_action_redirect(self):
        """Test that providing action will do correct redirect."""
        self.add_provider_to_user()

        redirect_url = self.saml_provider._get_auth_request({"a": "action"})
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
        self.assertEqual(
            response.url,
            self.base_url() + "/odoo#action=action",
        )

    def test_menu_redirect(self):
        """Test that providing menu will do correct redirect."""
        self.add_provider_to_user()

        redirect_url = self.saml_provider._get_auth_request({"m": "12"})
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
        self.assertEqual(
            response.url,
            self.base_url() + "/odoo#menu_id=12",
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
    def test_download_metadata_no_provider(self):
        self.saml_provider.idp_metadata_url = "http://localhost:8000/metadata"
        self.saml_provider.idp_metadata = ""
        self.saml_provider.active = False
        self.saml_provider.action_refresh_metadata_from_url()
        self.assertFalse(self.saml_provider.idp_metadata)

    @responses.activate
    def test_download_metadata_error(self):
        responses.add(
            responses.GET,
            "http://localhost:8000/metadata",
            status=500,
            content_type="text/xml",
        )
        self.saml_provider.idp_metadata_url = "http://localhost:8000/metadata"
        self.saml_provider.idp_metadata = ""
        with self.assertRaises(UserError):
            self.saml_provider.action_refresh_metadata_from_url()
        self.assertFalse(self.saml_provider.idp_metadata)

    @responses.activate
    def test_download_metadata_no_update(self):
        expected_metadata = self.idp.get_metadata()
        responses.add(
            responses.GET,
            "http://localhost:8000/metadata",
            status=200,
            content_type="text/xml",
            body=expected_metadata,
        )
        self.saml_provider.idp_metadata_url = "http://localhost:8000/metadata"
        self.saml_provider.idp_metadata = expected_metadata
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

    @responses.activate
    def test_login_with_saml_unsigned_response(self):
        self.add_provider_to_user()
        self.saml_provider.idp_metadata_url = "http://localhost:8000/metadata"
        unsigned_idp = UnsignedFakeIDP([self.saml_provider._metadata_string()])
        redirect_url = self.saml_provider._get_auth_request()
        self.assertIn("http://localhost:8000/sso/redirect?SAMLRequest=", redirect_url)

        response = unsigned_idp.fake_login(redirect_url)
        self.assertEqual(200, response.status_code)
        unpacked_response = response._unpack()

        responses.add(
            responses.GET,
            "http://localhost:8000/metadata",
            status=200,
            content_type="text/xml",
            body=self.saml_provider.idp_metadata,
        )
        with (
            self.assertRaises(SignatureError),
            mute_logger("saml2.entity"),
            mute_logger("saml2.client_base"),
        ):
            (database, login, token) = (
                self.env["res.users"]
                .sudo()
                .auth_saml(
                    self.saml_provider.id, unpacked_response.get("SAMLResponse"), None
                )
            )
