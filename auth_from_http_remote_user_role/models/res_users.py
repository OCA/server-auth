# Copyright 2018 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import fields, models


class ResUsers(models.Model):
    _inherit = 'res.users'

    last_http_header_roles = fields.Char(
        string='Last HTTP header roles'
    )

    def _update_last_http_header_roles(self):
        if self.env.context.get('change_roles'):
            return {}
        return {'last_http_header_roles': False}

    def write(self, vals):
        """Invalidate last_http_header_roles

        When roles or groups have been changed on User
        """
        if 'groups_id' in vals or 'role_line_ids' in vals:
            vals.update(self._update_last_http_header_roles())
        return super().write(vals)
