# Copyright 2018 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import api, fields, models


class ResUsersRole(models.Model):
    _inherit = 'res.users.role'

    user_role_code = fields.Char(
        string='HTTP header code'
    )

    @api.model
    def change_roles_remote_user(self, env, user_id, new_roles):
        """ Change the roles of the user with id user_id"""
        user = env['res.users'].browse(user_id)
        new_roles = set(new_roles)
        existing_roles = set(user.role_ids.ids)
        roles2add = list(new_roles.difference(existing_roles))
        roles2remove = list(existing_roles.difference(new_roles))
        if roles2add:
            triplets = [(0, False, {'role_id': roleid, 'user_id': user.id})
                        for roleid in roles2add]
            user.role_line_ids = triplets
        if roles2remove:
            env['res.users.role.line'].search([
                ('user_id', '=', user.id),
                ('role_id', 'in', roles2remove)]).unlink()
