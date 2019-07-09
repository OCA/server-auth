# Copyright 2019 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
# pylint: disable=missing-docstring,invalid-name
from odoo import _, api, fields, models

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

    dynamic_method_contract = fields.Selection(
        selection="_get_group_use_selection",
        string="Use contract",
        help="Include partners that a contract for a specific product")
    product_ids = fields.Many2many(
        comodel_name='product.product',
        relation='dynamic_group_product',
        column1='gid', column2='product_id',
        string="Products that grant group membership",
        help="Specify the products that, if present in a current contract"
             " for the user, make the user a member of this group.")

    @api.multi
    def dynamic_method_contract_check(self, user):
        """Check wether user has an active contract that gives group access."""
        self.ensure_one()
        self.env.cr.execute(
            COUNT_LINE_STATEMENT, (self.id, user.partner_id.id))
        kount = self.env.cr.fetchone()[0]
        message_parms = {
            'group': '%d:%s' % (self.id, self.display_name),
            'user': '%d:%s' % (user.id, user.display_name),
            'kount': kount,
        }
        self._debug_message(
            _("User %(user)s has %(kount)d contract lines for dynamic group %(group)s"),
            message_parms)
        return kount > 0
