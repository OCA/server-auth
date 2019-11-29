# © 2019 Savoir-faire Linux
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import common


class TestAuthSamlCreateUserCommon(common.TransactionCase):

    def setUp(self):
        super(TestAuthSamlCreateUserCommon, self).setUp()
        self.env.ref(
            'auth_saml.allow_saml_uid_and_internal_password').write(
                {'value': 1})

        # Usefull models
        self.SamlProvider = self.env['auth.saml.provider']
        self.ResUsers = self.env['res.users']

        self.provider = self.env.ref(
            'auth_saml_create_user.provider_local_create_user')
