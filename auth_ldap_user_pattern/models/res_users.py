# Copyright (C) 2019 IBM Corp.
# Copyright (C) 2019 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import re

from odoo import api, fields, models, registry, SUPERUSER_ID, _
from odoo.exceptions import UserError


class Users(models.Model):
    _inherit = "res.users"

    is_ldap_user = fields.Boolean(
        string='Is LDAP User',
    )

    @classmethod
    def _login(cls, db, login, password):
        """ Overload _login to check login string matches with pattern
        before passing to the super """
        login = login.lower()
        with registry(db).cursor() as cr:
            env = api.Environment(cr, SUPERUSER_ID, {})
            Ldap = env['res.company.ldap']
            for conf in Ldap.get_ldap_dicts():
                if conf['user_pattern']:
                    pattern = re.compile(conf['user_pattern'])
                    if pattern.match(login):
                        # Bypass Standard Odoo authentication and only check
                        # user id
                        entry = Ldap.authenticate(conf, login, password)
                        if entry:
                            user_id = Ldap.get_or_create_user(
                                conf, login, entry)
                            if user_id:
                                return user_id
        return super(Users, cls)._login(db, login, password)


class ChangePasswordUser(models.TransientModel):
    _inherit = 'change.password.user'

    @api.multi
    def change_password_button(self):
        for line in self:
            if not line.new_passwd:
                raise UserError(_("Before clicking on 'Change Password', "
                                  "you have to write a new password."))
            if line.user_id.is_ldap_user and not line.user_id.has_group(
                    'auth_ldap_user_pattern.group_ldap_password_change'):
                raise UserError(_("Sorry, You can not change password for "
                                  "LDAP User!"))
        res = super(ChangePasswordUser, self).change_password_button()
        return res
