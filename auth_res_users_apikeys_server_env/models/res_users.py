# Copyright 2018 ACSONE SA/NV
# Copyright 2021 Camptocamp SA
# @author: Simone Orsi <simone.orsi@camptocamp.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).


from odoo import models
from odoo.tools.config import config
from odoo.exceptions import AccessDenied


class ResUsers(models.Model):

    _inherit = "res.users"

    

    def _check_credentials(self, password, user_agent_env):
        try:
            return super()._check_credentials(password, user_agent_env)
        except AccessDenied:
            pass

        if self.env['res.users.apikeys']._check_credentials(scope=f'rpc_{config.get("running_env", "")}', key=password) == self.env.uid:
            return

        raise AccessDenied()