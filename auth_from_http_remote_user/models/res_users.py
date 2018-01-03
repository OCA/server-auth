# Author: Laurent Mignon
# Copyright 2014-2018 'ACSONE SA/NV'
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

import odoo
from odoo import fields, models
from odoo.addons.auth_from_http_remote_user import utils


class Users(models.Model):
    _inherit = 'res.users'

    sso_key = fields.Char(
        'SSO Key',
        size=utils.KEY_LENGTH,
        readonly=True,
        copy=False
    )

    def check_credentials(self, password):
        res = self.sudo().search([('id', '=', self._uid),
                                  ('sso_key', '=', password)])
        if not res:
            return super(Users, self).check_credentials(password)

    @classmethod
    def check(cls, db, uid, passwd):
        try:
            return super(Users, cls).check(db, uid, passwd)
        except odoo.exceptions.AccessDenied:
            if not passwd:
                raise
            registry = odoo.registry(db)
            with registry.cursor() as cr:
                cr.execute('''SELECT COUNT(1)
                                FROM res_users
                               WHERE id=%s
                                 AND sso_key=%s
                                 AND active=%s''', (int(uid), passwd, True))
                if not cr.fetchone()[0]:
                    raise
                cls._uid_cache.setdefault(db, {})[uid] = passwd
