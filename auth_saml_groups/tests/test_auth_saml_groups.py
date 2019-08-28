# © 2019 Savoir-faire Linux
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from .common import TestAuthSamlGroupsCommon
from .saml_args import provider, validation, saml_response


class TestAuthSamlGroups(TestAuthSamlGroupsCommon):

    def setUp(self):
        super(TestAuthSamlGroups, self).setUp()

    def sign_in(self):
        return self.ResUsers.auth_saml(
            provider, saml_response)

    def test_010_group_assignment(self):
        self.assertEqual(len(self.test_user.groups_id), 0)
        self.sign_in()
        self.assertIn(
            self.env.ref('base.group_user'),
            self.test_user.groups_id)

    def test_020_auth_saml_signin(self):
        user_credentials = self.sign_in()
        self.assertEqual(
            user_credentials[1],
            self.test_user.login)

    def test_030__auth_saml_signin(self):
        saml_validate = self.ResUsers._auth_saml_validate(
            provider, saml_response)
        attrs = saml_validate[1]
        login = self.ResUsers._auth_saml_signin(
            provider, validation, saml_response, attrs)
        self.assertEqual(login, self.test_user.login)

    def test_040_set_user_groups(self):
        saml_validate = self.ResUsers._auth_saml_validate(
            provider, saml_response)
        saml_uid = validation['user_id']
        attrs = saml_validate[1]
        user_ids = self.ResUsers.search(
            [('saml_uid', '=', saml_uid), ('saml_provider_id', '=', provider)])
        user = user_ids[0]
        self.ResUsers._set_user_groups(user, provider, attrs)
