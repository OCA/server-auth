# Copyright 2019 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
# pylint: disable=missing-docstring,protected-access,invalid-name
from odoo.tests import common


class TestAuthDynamicGroups(common.TransactionCase):
    post_install = True
    at_install = False

    def setUp(self):
        """Superclass provides a relation between an NGO and a volunteer."""
        super(TestAuthDynamicGroups, self).setUp()
        main_company = self.env.ref('base.main_partner')
        self.demo_user = self.env.ref('base.user_demo')
        self.demo_partner = self.demo_user.partner_id
        self.relation_type_model = self.env['res.partner.relation.type']
        self.selection_model = self.env['res.partner.relation.type.selection']
        self.relation_model = self.env['res.partner.relation']
        # Create a relation type linking NGO's with volunteers.
        self.type_ngo2volunteer = self.relation_type_model.create({
            'name': 'NGO has volunteer',
            'name_inverse': 'volunteer works for NGO',
            'contact_type_left': 'c',
            'contact_type_right': 'p'})
        # Create a relation from NGO to volunteer.
        self.company_user_relation = self.relation_model.create({
            'type_id': self.type_ngo2volunteer.id,
            'left_partner_id': main_company.id,
            'right_partner_id': self.demo_partner.id})
        # Find the selection type from volunteer to NGO.
        self.selection_volunteer2ngo = self.selection_model.search([
            ('type_id', '=', self.type_ngo2volunteer.id),
            ('is_inverse', '=', True)], limit=1)

    def test_auth_dynamic_groups(self):
        """Test adding volunteers to our volunteer group."""
        group = self.env['res.groups'].create({
            'name': 'Test dynamic group volunteers',
            'is_dynamic': True,
            'dynamic_method_relation': 'use',
            'relation_type_ids':
                [(6, False, [self.selection_volunteer2ngo.id])]})
        self.assertTrue(group.dynamic_method_relation_check(self.demo_user))
        self.assertTrue(group.should_be_in(self.demo_user))
        group.action_refresh_users()
        self.assertIn(self.demo_user, group.users)
        group.write({'users': [(6, False, [])]})
        self.assertFalse(group.users)
        self.env['res.users'].update_dynamic_groups(self.demo_user.id)
        self.assertIn(self.demo_user, group.users)
        # Check relation expiration
        self.company_user_relation.write({'date_end': '2018-12-31'})
        self.env['res.users'].update_dynamic_groups(self.demo_user.id)
        self.assertNotIn(self.demo_user, group.users)
