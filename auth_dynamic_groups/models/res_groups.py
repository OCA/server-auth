# Copyright 2013-2019 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
# pylint: disable=missing-docstring,invalid-name,no-self-use,protected-access
import logging

from odoo import _, api, exceptions, fields, models
from odoo.tools.safe_eval import safe_eval


_logger = logging.getLogger(__name__)


class ResGroups(models.Model):
    _inherit = 'res.groups'

    is_dynamic = fields.Boolean(string='Dynamic', index=True)
    is_automatic = fields.Boolean(string='Filled programmatically')
    enable_debug = fields.Boolean(string='Display detailed debug messages')

    def _get_group_use_selection(self):
        """Get values that determine how conditions should be used."""
        return[
            ('ignore', 'Do not use this condition'),
            ('exclude', 'Exclude user from group'),
            ('include', 'Include user in group'),
            ('use', 'Include if all used conditions satisfied'),
        ]

    # Fields to support selection by formula.
    dynamic_method_formula = fields.Selection(
        selection="_get_group_use_selection",
        string="Use formula",
        help="Specify wether to include users based on formula")
    dynamic_group_condition = fields.Text(
        string='Condition',
        default='False',
        help="The condition to be met for a user to be a member"
             " of this group.\n"
             "It is evaluated as python code at login time,"
             " you get `user` passed as a browse record")

    # Fields to support selection by category.
    dynamic_method_category = fields.Selection(
        selection="_get_group_use_selection",
        string="Use partner category",
        help="Specify wether to include users based on partner category")
    partner_category_ids = fields.Many2many(
        comodel_name='res.partner.category',
        relation='dynamic_group_partner_category',
        column1='gid', column2='category_id',
        string="Partner categories",
        help="Used when selection is based on partner category.")

    @api.multi
    def action_refresh_users(self):
        """Refresh the users in this group.

        Limit this to 512 users, to prevent huge performance problems.
        """
        res_users = self.env['res.users']
        for this in self.filtered('is_dynamic'):
            for user in res_users.search([], limit=512):
                this.update_group_user(user)

    @api.multi
    def update_group_user(self, user):
        """Update membership for a single user."""
        self.ensure_one()
        message_parms = {
            'group': '%d:%s' % (self.id, self.display_name),
            'user': '%d:%s' % (user.id, user.display_name),
        }
        self._debug_message(
            _("Check user %(user)s for membership of dynamic group %(group)s"),
            message_parms)
        should_be_in = self.should_be_in(user)
        if should_be_in:
            if user in self.users:
                self._debug_message(
                    _("User %(user)s already member of group %(group)s"), message_parms)
                return
            self._add_group_user(user)
            _logger.info(
                _("User %(user)s added to dynamic group %(group)s"), message_parms)
            return
        if user not in self.users:
            self._debug_message(
                _("User %(user)s is not a member of group %(group)s"), message_parms)
            return
        self._remove_group_user(user)
        _logger.info(
            _("User %(user)s removed from dynamic group %(group)s"), message_parms)

    def _add_group_user(self, user):
        """Add a single member to the group."""
        self.env.cr.execute(
            'INSERT INTO res_groups_users_rel (uid, gid) VALUES (%s, %s)',
            (user.id, self.id),
        )
        self.env['res.users'].invalidate_cache(['groups_id'], [user.id])

    def _remove_group_user(self, user):
        """Remove a single member from the group."""
        self.env.cr.execute(
            'DELETE FROM res_groups_users_rel'
            ' WHERE uid=%s AND gid=%s',
            (user.id, self.id),
        )
        self.env['res.users'].invalidate_cache(['groups_id'], [user.id])

    @api.multi
    def should_be_in(self, user):
        """Determine wether user should be in group."""
        self.ensure_one()
        if not self.is_dynamic:
            return user in self.users  # For completeness sake
        in_group = False
        include_seen = False
        criteria = self._get_criteria()
        for criterium, use in criteria.items():
            method = getattr(self, '%s_check' % criterium)
            satisfied = method(user)
            in_group = satisfied
            if satisfied:
                if use == 'exclude':
                    return False
                if use == 'include':
                    include_seen = True
        return include_seen or in_group

    @api.multi
    def _get_criteria(self):
        """Get values for all criteria fields, unless ignored."""
        self.ensure_one()
        assert self.is_dynamic
        criteria = {
            name: self[name]
            for name in self._fields.keys()
            if name[:15] == 'dynamic_method_' and
            self[name] and self[name] != 'ignore'
        }
        return criteria or {'dynamic_method_formula': 'use'}

    @api.multi
    def dynamic_method_formula_check(self, user):
        """Check wether user satisfies formula."""
        self.ensure_one()
        return safe_eval(
            self.dynamic_group_condition or 'False',
            {'dynamic_group': self,
             'user': user,
             'any': any,
             'all': all,
             'filter': filter})

    @api.multi
    def dynamic_method_category_check(self, user):
        """Check wether user-partner has defined category."""
        self.ensure_one()
        for category in self.partner_category_ids:
            if category in user.partner_id.category_id:
                return True
        return False

    @api.multi
    @api.constrains('dynamic_method_formula', 'dynamic_group_condition')
    def _check_dynamic_group_condition(self):
        try:
            for this in self:
                if this.dynamic_method_formula and \
                        this.dynamic_method_formula != 'ignore':
                    this.dynamic_method_formula_check(self.env.user)
        except (NameError, SyntaxError, TypeError):
            raise exceptions.ValidationError(
                _("The condition doesn't evaluate correctly!"))

    def _debug_message(self, message, message_parms):
        """Only log detailed messages if requested."""
        if not self.enable_debug:
            return
        _logger.debug(message, message_parms)
