# Copyright (C) 2018 Brainbean Apps
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import models


class Users(models.Model):
    _inherit = 'res.users'

    def _check_credentials(self, password):
        try:
            super()._check_credentials(password)
        finally:
            Ldap = self.env['res.company.ldap']
            for conf in Ldap._get_ldap_dicts():
                if Ldap._update_user(conf, self):
                    break
