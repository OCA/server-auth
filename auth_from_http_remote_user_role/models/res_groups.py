# Copyright 2018 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import models


class ResGroups(models.Model):
    _inherit = 'res.groups'

    def unlink(self):
        """Invalidate last_http_header_roles
        """
        self.users.write({
            'last_http_header_roles': False,
        })
        return super().unlink()

    def write(self, vals):
        """Invalidate last_http_header_roles
        """
        res = super().write(vals)
        if 'users' in vals:
            # Make it simple, this use case should be rare
            # thus invalidate the http_header on all users
            self.mapped('users').write({
                'last_http_header_roles': False,
            })
        return res

    def create(self, vals):
        """Invalidate last_http_header_roles
        """
        rec = super().create(vals)
        if 'users' in vals:
            rec.users.write({
                'last_http_header_roles': False,
            })
        return rec
