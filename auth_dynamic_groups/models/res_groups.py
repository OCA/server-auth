# -*- coding: utf-8 -*-
# Copyright 2013-2019 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
# pylint: disable=missing-docstring,invalid-name,no-self-use
import logging

from odoo import _, api, exceptions, fields, models
from odoo.tools.safe_eval import safe_eval


_logger = logging.getLogger(__name__)


class ResGroups(models.Model):
    _inherit = 'res.groups'

    @api.depends('group_type')
    def _compute_dynamic(self):
        """Is group membership maintained manually or automatically?"""
        for this in self:
            this.is_dynamic = this.group_type != 'manual'

    group_type = fields.Selection(
        selection=[
            ('manual', 'Users are added by admins'),
            ('auto', 'Users are added (or removed) programmatically'),
            ('formula', 'Based on formula'),
            ('partner_category', 'Based on partner category')],
        string="Selection criteria",
        default='manual',
        required='True',
        help="Specify how users should selected to belong to this group")
    is_dynamic = fields.Boolean(
        compute='_compute_dynamic',
        string='Dynamic',
        store=True, index=True)
    dynamic_group_condition = fields.Text(
        string='Condition',
        default='False',
        help="The condition to be met for a user to be a member"
             " of this group.\n"
             "It is evaluated as python code at login time,"
             " you get `user` passed as a browse record")
    partner_category_ids = fields.Many2many(
        comodel_name='res.partner.category',
        relation='dynamic_group_partner_category',
        column1='gid', column2='category_id',
        string="Partner categories",
        help="Used when selection is based on partner category.")

    @api.multi
    def should_be_in(self, user):
        """Determine wether user should be in group."""
        self.ensure_one()
        if self.group_type == 'formula':
            return self.eval_dynamic_group_condition(user)
        if self.group_type == 'partner_category':
            for category in self.partner_category_ids:
                if category in user.partner_id.category_id:
                    return True
            return False
        return user in self.users  # For completeness sake

    @api.multi
    def eval_dynamic_group_condition(self, user):
        self.ensure_one()
        assert self.group_type == 'formula'
        return safe_eval(
            self.dynamic_group_condition or 'False',
            {'dynamic_group': self,
             'user': user,
             'any': any,
             'all': all,
             'filter': filter})

    @api.multi
    @api.constrains('group_type', 'dynamic_group_condition')
    def _check_dynamic_group_condition(self):
        try:
            for this in self.filtered(lambda r: r.group_type == 'formula'):
                this.eval_dynamic_group_condition(self.env.user)
        except (NameError, SyntaxError, TypeError):
            raise exceptions.ValidationError(
                _('The condition doesn\'t evaluate correctly!'))

    @api.multi
    def update_group_user(self, user):
        """Update membership for a single user."""
        self.ensure_one()
        should_be_in = self.should_be_in(user)
        if should_be_in:
            if user in self.users:
                _logger.debug(
                    _("User %s already member of group %s"),
                    user.display_name, self.display_name)
                return
            self.write({'users': [(4, user.id, False)]})
            _logger.info(
                _("User %s added to dynamic group %s"),
                user.display_name, self.display_name)
            return
        if user not in self.users:
            _logger.debug(
                _("User %s is not a member of group %s"),
                user.display_name, self.display_name)
            return
        self.write({'users': [(3, user.id, False)]})  # remove
        _logger.info(
            _("User %s removed from dynamic group %s"),
            user.display_name, self.display_name)

    @api.multi
    def action_refresh_users(self):
        """Refresh the users in this group."""
        self.ensure_one()
        assert self.is_dynamic
        res_users = self.env['res.users']
        for user in res_users.search([]):
            self.update_group_user(user)

    @api.model
    def create(self, vals):
        """Support existing code that sets dynamic."""
        vals = self._update_vals(vals)
        return super(ResGroups, self).create(vals)

    @api.multi
    def write(self, vals):
        """Support existing code that sets dynamic."""
        vals = self._update_vals(vals)
        return super(ResGroups, self).write(vals)

    def _update_vals(self, vals):
        """Support existing code that sets dynamic."""
        if 'is_dynamic' in vals and 'group_type' not in vals:
            is_dynamic = vals.get('is_dynamic')
            vals['group_type'] = 'formula' if is_dynamic else 'manual'
        return vals
