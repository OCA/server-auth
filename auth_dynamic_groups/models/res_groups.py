# -*- coding: utf-8 -*-
# Copyright 2013-2019 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import _, api, exceptions, fields, models
from odoo.tools.safe_eval import safe_eval


class ResGroups(models.Model):
    _inherit = 'res.groups'

    is_dynamic = fields.Boolean('Dynamic')
    dynamic_group_condition = fields.Text(
        'Condition', help='The condition to be met for a user to be a '
        'member of this group. It is evaluated as python code at login '
        'time, you get `user` passed as a browse record')

    @api.multi
    def eval_dynamic_group_condition(self, uid=None):
        user = self.env['res.users'].browse([uid]) if uid else self.env.user
        result = all(
            self.mapped(
                lambda this: safe_eval(
                    this.dynamic_group_condition or 'False',
                    {
                        'user': user.sudo(),
                        'any': any,
                        'all': all,
                        'filter': filter,
                    })))
        return result

    @api.multi
    @api.constrains('dynamic_group_condition')
    def _check_dynamic_group_condition(self):
        try:
            self.filtered('is_dynamic').eval_dynamic_group_condition()
        except (NameError, SyntaxError, TypeError):
            raise exceptions.ValidationError(
                _('The condition doesn\'t evaluate correctly!'))

    @api.multi
    def action_evaluate(self):
        res_users = self.env['res.users']
        for user in res_users.search([]):
            res_users.update_dynamic_groups(user.id, self.env.cr.dbname)
