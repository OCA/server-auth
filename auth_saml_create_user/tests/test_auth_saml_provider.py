# © 2019 Savoir-faire Linux
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.exceptions import AccessDenied

from odoo.addons.auth_saml.tests.test_pysaml import TestPySaml


class TestSamlCreateUser(TestPySaml):
    def setUp(self):
        super().setUp()

    def test_login_with_existing_user(self):
        # Update the existing user login, to avoid already existing user
        # when creating a new one by SAML
        self.user.unlink()

        redirect_url = self.saml_provider._get_auth_request()
        self.assertIn("http://localhost:8000/sso/redirect?SAMLRequest=", redirect_url)

        response = self.idp.fake_login(redirect_url)
        self.assertEqual(200, response.status_code)
        unpacked_response = response._unpack()

        self.assertFalse(
            self.env["res.users"].search([("login", "=", "test@example.com")])
        )

        (database, login, token) = (
            self.env["res.users"]
            .sudo()
            .auth_saml(
                self.saml_provider.id, unpacked_response.get("SAMLResponse"), None
            )
        )

        # User is now created
        new_user = self.env["res.users"].search([("login", "=", "test@example.com")])
        self.assertTrue(new_user)

        # We should not be able to log in with the wrong token
        with self.assertRaises(AccessDenied):
            new_user._check_credentials(
                {"type": "password", "password": "WRONG_TOKEN"},
                {"interactive": True},
            )

        # User should now be able to log in with the token
        self.authenticate(user="test@example.com", password=token)
