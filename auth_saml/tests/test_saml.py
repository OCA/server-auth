import base64
import os
import json
import requests_mock

from odoo.tests import HttpCase, tagged
from odoo.exceptions import AccessDenied


@tagged("saml")
class TestSaml(HttpCase):
    def setUp(self):
        super().setUp()
        self.saml_provider = self.env.ref("auth_saml.provider_local")
        self.url_saml_request = "/auth_saml/get_auth_request?pid=%d" % self.saml_provider.id

    def get_saml_response(self):
        response_path = os.path.join(os.path.dirname(__file__), 'data', 'saml_response.xml')
        with open(response_path) as response_file:
            response_str = response_file.read()
        response_b64 = base64.b64decode(response_str)
        return response_b64

    def test_01_login_using_a_token(self):
        """Log-in using an user without password but a SAML token"""
        # Create an user with only password
        user = self.env["res.users"].with_context(no_reset_password=True).create({
            "name": "User with Token",
            "email": "saml@example.com",
            "login": "saml@example.com",
            "password": "standard_password",
        })

        # Standard login using password
        self.authenticate(user="saml@example.com", password="standard_password")
        self.assertEqual(self.session.uid, user.id)

        # SAML provider should be listed in the login page
        self.logout()
        response = self.url_open('/')
        self.assertIn('SAML Provider Demo', response.text)
        self.assertIn(self.url_saml_request, response.text)

        # If the URL for the SAML provided is consumed, it should redirect to the location
        # configured in the provider
        with requests_mock.Mocker(real_http=True) as m:
            m.register_uri('GET', '/idp/saml2/sso', text='SAML Login Page')
            response = self.url_open(self.url_saml_request)
        self.assertIn('SAML Login Page', response.text)

        # Try to log-in with an unexisting SAML token
        with self.assertRaises(AccessDenied):
            self.authenticate(user="saml@example.com", password="test_saml_token")

        self.url_open('/auth_saml/signin', params={
            'SAMLResponse': self.get_saml_response(),
            'RelayState': json.dumps({
                'd': self.env.cr.dbname,
                'p': self.saml_provider.id,
                'context': {},
            }),
        })

        # Create a SAML token and try again
        print()
