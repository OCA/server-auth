# Copyright 2024 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo import fields, models


class ResUsers(models.Model):
    _inherit = "res.users"

    has_password = fields.Boolean(compute="_compute_has_password")

    def _compute_has_password(self):
        # Bypass ORM as password is always empty in cache
        self.env.cr.execute(
            """SELECT id, password FROM res_users WHERE id IN %s;""", (tuple(self.ids),)
        )
        res = {row[0]: row[1] for row in self.env.cr.fetchall()}
        for user in self:
            user.has_password = bool(res.get(user.id))

    def _empty_password(self):
        # Update in DB to avoid using crypt context
        self.env.cr.execute(
            """UPDATE res_users SET password = %s WHERE id IN %s""",
            ("", (tuple(self.ids),)),
        )
