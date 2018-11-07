# Copyright 2018 Brainbean Apps
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import models


class ResUsers(models.Model):
    _inherit = 'res.users'

    def _check_credentials(self, password):
        try:
            super()._check_credentials(password)
        finally:
            ldap_configs = self.env['res.company.ldap'].sudo().search([
                ('ldap_server', '!=', False),
            ], order='sequence')
            for ldap_config in ldap_configs:
                if ldap_config._update_group_membership(self):
                    break
