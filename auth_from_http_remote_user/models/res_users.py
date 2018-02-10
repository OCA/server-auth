# Author: Laurent Mignon
# Copyright 2014-2018 'ACSONE SA/NV'
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import fields, models
from .. import utils


class Users(models.Model):
    _inherit = 'res.users'

    sso_key = fields.Char(
        'SSO Key',
        size=utils.KEY_LENGTH,
        readonly=True,
        copy=False
    )

    def check_credentials(self, password):
        """Check credentials for SSO user"""
        res = self.sudo().search([('id', '=', self._uid),
                                  ('sso_key', '=', password)])
        if not res:
            return super(Users, self).check_credentials(password)
