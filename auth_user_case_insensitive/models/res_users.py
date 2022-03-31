# Copyright 2015-2017 LasLabs Inc.
# Copyright 2021 Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import api, fields, models


class ResUsers(models.Model):

    _inherit = "res.users"

    login = fields.Char(help="Used to log into the system. Case insensitive.")

    @classmethod
    def _login(cls, db, login, password, user_agent_env):
        """Overload _login to lowercase the `login` before passing to the
        super"""
        login = login.lower()
        return super(ResUsers, cls)._login(
            db, login, password, user_agent_env=user_agent_env
        )

    @api.model_create_multi
    def create(self, vals_list):
        """Overload create multiple to lowercase login"""
        for val in vals_list:
            val["login"] = val.get("login", "").lower()
        return super(ResUsers, self).create(vals_list)

    def write(self, vals):
        """Overload write to lowercase login"""
        if vals.get("login"):
            vals["login"] = vals["login"].lower()
        return super(ResUsers, self).write(vals)
