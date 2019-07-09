# -*- coding: utf-8 -*-
# Copyright 2019 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
# pylint: disable=missing-docstring,protected-access,invalid-name
from odoo.tests.common import TransactionCase


class TestAuthDynamicGroups(TransactionCase):

    post_install = True
    at_install = False

    def setUp(self):
        """We need a group, a product that gives access to that group,
        and a contract that includes this product."""
        super(TestAuthDynamicGroups, self).setUp()
        # Make sure a sale journal is present for tests
        sequence_model = self.env['ir.sequence']
        contract_sequence = sequence_model.create({
            'company_id': self.env.user.company_id.id,
            'code': 'contract',
            'name': 'contract sequence',
            'number_next': 1,
            'implementation': 'standard',
            'padding': 3,
            'number_increment': 1})
        journal_model = self.env['account.journal']
        journal_model.create({
            'company_id': self.env.user.company_id.id,
            'code': 'contract',
            'name': 'contract journal',
            'sequence_id': contract_sequence.id,
            'type': 'sale'})
        # Create products:
        uom_unit = self.env.ref('product.product_uom_unit')
        product_model = self.env['product.product']
        self.product_newsletter_subscription = product_model.create({
            'name': 'Test newsletter_subscription',
            'type': 'service',
            'uom_id': uom_unit.id,
            'uom_po_id': uom_unit.id})
        # Create contract with newsletter subscription:
        contract_model = self.env['account.analytic.account']
        line_model = self.env['account.analytic.invoice.line']
        self.demo_user = self.env.ref('base.user_demo')
        contract_demo_user = contract_model.create({
            'name': 'Test Contract Demo User',
            'partner_id': self.demo_user.partner_id.id,
            'recurring_invoices': True,
            'date_start': '2016-02-15',
            'recurring_next_date': '2016-02-29'})
        line_model.create({
            'analytic_account_id': contract_demo_user.id,
            'product_id': self.product_newsletter_subscription.id,
            'name': self.product_newsletter_subscription.name,
            'quantity': 1,
            'uom_id': self.product_newsletter_subscription.uom_id.id,
            'price_unit': 25.0})

    def test_auth_dynamic_groups(self):
        group = self.env['res.groups'].create({
            'name': 'dynamic group',
            'is_dynamic': True,
            'is_contract_based': True})
        self.product_newsletter_subscription.write(
            {'dynamic_group_ids': [(6, False, [group.id])]})
        self.assertTrue(self.demo_user.has_group_contract(group))
        group.action_evaluate()
        self.assertIn(self.demo_user, group.users)
        group.write({'users': [(6, False, [])]})
        self.assertFalse(group.users)
        self.env['res.users'].update_dynamic_groups(self.demo_user.id)
        self.assertIn(self.demo_user, group.users)
