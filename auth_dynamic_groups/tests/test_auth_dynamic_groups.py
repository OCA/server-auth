# -*- coding: utf-8 -*-
# Copyright 2019 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
# pylint: disable=missing-docstring,protected-access
from odoo.tests.common import TransactionCase
from odoo import exceptions


class TestAuthDynamicGroups(TransactionCase):
    post_install = True
    at_install = False

    def test_formula(self):
        demo_user = self.env.ref('base.user_demo')
        groups_model = self.env['res.groups']
        group = groups_model.create({
            'name': 'Test formula group Demo users',
            'group_type': 'formula',
            'dynamic_group_condition': "'Demo' in user.name"})
        self.assertTrue('Demo' in demo_user.name)
        self.dynamic_group_user_test(group, demo_user)
        # Redundant extra call should just lead to debug message.
        user_model = self.env['res.users']
        user_model.update_dynamic_groups(demo_user.id)
        demo_user.name = 'Test name without de D word'
        user_model.update_dynamic_groups(demo_user.id)
        self.assertNotIn(demo_user, group.users)
        # Redundant extra call should just lead to debug message.
        user_model.update_dynamic_groups(demo_user.id)

    def test_invalid_formula(self):
        """Invalid formula should result in exception."""
        groups_model = self.env['res.groups']
        with self.assertRaises(exceptions.ValidationError):
            groups_model.create({
                'name': 'Test invalid formula',
                'group_type': 'formula',
                'dynamic_group_condition': '1 = 0'})

    def test_old_stype(self):
        groups_model = self.env['res.groups']
        group = groups_model.create({
            'name': 'Test formula is_dynamic',
            'is_dynamic': 'formula',
            'dynamic_group_condition': "'Demo' in user.name"})
        self.assertEqual(group.group_type, 'formula')

    def test_partner_category(self):
        demo_user = self.env.ref('base.user_demo')
        category_model = self.env['res.partner.category']
        category = category_model.create({'name': 'Test portal category'})
        demo_user.write({'category_id': [(4, category.id, False)]})
        groups_model = self.env['res.groups']
        group = groups_model.create({
            'name': 'Test partner_category group Portal users',
            'group_type': 'partner_category',
            'partner_category_ids': [(6, False, [category.id])]})
        self.assertTrue(category in demo_user.category_id)
        self.dynamic_group_user_test(group, demo_user)

    def dynamic_group_user_test(self, group, user):
        """Do tests with user that should be in group."""
        group.action_refresh_users()
        self.assertIn(user, group.users)
        group.write({'users': [(6, False, [])]})
        self.assertFalse(group.users)
        self.env['res.users'].update_dynamic_groups(user.id)
        self.assertIn(user, group.users)

    def test_login(self):
        """Just check that login call does not result in error.

        login uses a separate environment/cursor so does not know about
        our new group, nor can we check result of login.
        """
        self.env['res.users']._login(self.env.cr.dbname, 'demo', 'demo')

    def test_not_dynamic(self):
        """Check a non dynamic group."""
        groups_model = self.env['res.groups']
        group = groups_model.create({
            'name': 'Just a group without members'})
        self.assertEqual(group.group_type, 'manual')
        demo_user = self.env.ref('base.user_demo')
        self.assertFalse(group.should_be_in(demo_user))
