# -*- coding: utf-8 -*-
# Copyright 2019 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
# pylint: disable=missing-docstring,invalid-name
import logging

from odoo import _, api, fields, models


_logger = logging.getLogger(__name__)

COUNT_LINE_STATEMENT = """\
SELECT COUNT(*) AS kount
 FROM dynamic_group_product dgp
 JOIN account_analytic_invoice_line AS aail
   ON dgp.product_id = aail.product_id
 JOIN account_analytic_account AS aaa
   ON aail.analytic_account_id = aaa.id
 WHERE dgp.gid = %s
   AND aaa.partner_id = %s
   AND (aaa.date_start IS NULL or aaa.date_start <= CURRENT_DATE)
   AND (aaa.date_end IS NULL or aaa.date_end >= CURRENT_DATE)
"""


class ResGroups(models.Model):
    _inherit = 'res.groups'

    group_type = fields.Selection(
        selection_add=[('contract', 'Based on contracts for products')])
    product_ids = fields.Many2many(
        comodel_name='product.product',
        relation='dynamic_group_product',
        column1='gid', column2='product_id',
        string="Products that grant group membership",
        help="Specify the products that, if present in a current contract"
             " for the user, make the user a member of this group.")

    @api.multi
    def should_be_in(self, user):
        """Determine wether user should be in group."""
        self.ensure_one()
        if self.group_type == 'contract':
            return self.has_user_contract(user)
        return super(ResGroups, self).should_be_in(user)

    @api.multi
    def has_user_contract(self, user):
        """Check wether user has an active contract that gives group access."""
        self.ensure_one()
        self.env.cr.execute(
            COUNT_LINE_STATEMENT, (self.id, user.partner_id.id))
        kount = self.env.cr.fetchone()[0]
        _logger.info(
            _("User %s has %d contract lines for dynamic group %s"),
            user.display_name, kount, self.display_name)
        return kount > 0
