# © 2019 Savoir-faire Linux
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from .common import TestAuthSamlCreateUserCommon
from .arguments import provider, validation, saml_response


class TestAuthSamlCreateUser(TestAuthSamlCreateUserCommon):

    def setUp(self):
        super(TestAuthSamlCreateUser, self).setUp()

    def test_010_auth_saml_signin(self):
        self.ResUsers._auth_saml_signin(
            provider, validation, saml_response)

    def test_020_check_if_should_create_user(self):
        self.assertEqual(
            self.provider.create_user,
            self.ResUsers.check_if_create_user(self.provider.id))

    def test_030_create_user(self):
        saml_uid = 'new_test_user12312az@test.com'
        user_ids = self.ResUsers.search(
            [('saml_uid', '=', saml_uid)])
        self.assertTrue(not user_ids)
        self.ResUsers.create_user(saml_uid, provider)
        user_ids = self.ResUsers.search(
            [('saml_uid', '=', saml_uid)])
        self.assertTrue(user_ids)
