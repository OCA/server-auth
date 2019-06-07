# Copyright 2018 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import models


class ResUsersRoleLine(models.Model):
    _inherit = 'res.users.role.line'

    def unlink(self):
        """Invalid user.last_http_header_roles when a role line is
        deleted.
        """
        for line in self:
            line.user_id.last_http_header_roles = False
        return super().unlink()

    def write(self, vals):
        """Invalid user.last_http_header_roles when a role line is
        edited.
        """
        for line in self:
            line.user_id.last_http_header_roles = False
        return super().write(vals)

    def create(self, vals):
        """Invalid user.last_http_header_roles when a role line is
        created.
        """
        rec = super().create(vals)
        rec.user_id.last_http_header_roles = False
        return rec
