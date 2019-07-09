# -*- coding: utf-8 -*-
# Copyright 2013-2019 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
# pylint: disable=missing-docstring,invalid-name
from odoo import api, models, SUPERUSER_ID


class ResUsers(models.Model):
    _inherit = 'res.users'

    @classmethod
    def _login(cls, db, login, password):
        uid = super(ResUsers, cls)._login(db, login, password)
        if uid and uid != SUPERUSER_ID:
            with cls.pool.cursor() as cr:
                self = api.Environment(cr, SUPERUSER_ID, {})[cls._name]
                self.update_dynamic_groups(uid)
        return uid

    @api.model
    def update_dynamic_groups(self, uid):
        """Update membership of dynamic groups for a single user.

        This method must be called with admin rights active.
        """
        user = self.browse(uid)
        groups_model = self.env['res.groups']
        dynamic_groups = groups_model.search([('is_dynamic', '=', True)])
        for group in dynamic_groups:
            group.update_group_user(user)

    @api.multi
    def action_refresh_groups(self):
        """Refresh the users in this group."""
        for this in self:
            this.update_dynamic_groups(this.id)
