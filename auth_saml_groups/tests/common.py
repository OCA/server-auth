# © 2019 Savoir-faire Linux
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import common


class TestAuthSamlGroupsCommon(common.TransactionCase):
    def setUp(self):
        super(TestAuthSamlGroupsCommon, self).setUp()

        self.env.ref(
            'auth_saml.allow_saml_uid_and_internal_password').write(
                {'value': 1})
        self.SamlProvider = self.env['auth.saml.provider']
        self.ResUsers = self.env['res.users']
        self.provider = self.env.ref(
            'auth_saml_groups.provider_local_saml_groups')
        self.GroupMapping = \
            self.env['auth.saml.provider.group_mapping']
        self.test_mapping = self.GroupMapping.create({
            'saml_attribute': 'eduPersonAffiliation',
            'operator': 'equals',
            'value': 'group2',
            'group_id': self.env.ref('base.group_user').id,
            'saml_id': self.provider.id
        })
        self.provider.write({
            'group_mapping_ids': [(6, 0, [self.test_mapping.id])]
        })
        self.test_user = self.ResUsers.create({
            'name': 'Test User',
            'login': 'user2@example.com',
            'saml_provider_id': self.provider.id,
            'saml_uid': 'user2@example.com',
            'groups_id': [(6, 0, [])]
        })
