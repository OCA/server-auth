# Copyright 2018 Therp BV <https://therp.nl>
# Copyright 2018 Brainbean Apps <https://brainbeanapps.com>
# Copyright 2026 Invitu <https://www.invitu.com>
# Copyright 2026 eurodata CZ - Tomáš Dinkov
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import models


class ResUsers(models.Model):
    _inherit = "res.users"

    def _login(self, credential, user_agent_env):
        # Odoo 19: _login is an instance method working in self.env
        # (no separate cursor / db argument anymore, see auth_ldap).
        # _login raises AccessDenied on failure, so auth_info is always set here
        auth_info = super()._login(credential, user_agent_env=user_agent_env)
        login = credential["login"]
        user = self.env["res.users"].sudo().browse(auth_info["uid"])
        # check if this user came from ldap, rerun get_or_create_user in
        # this case to apply ldap groups if necessary
        ldaps = user.company_id.ldaps
        if user.active and any(ldaps.mapped("only_ldap_groups")):
            for conf in ldaps._get_ldap_dicts():
                entry = ldaps._authenticate(conf, login, credential["password"])
                if entry:
                    ldaps._get_or_create_user(conf, login, entry)
                    break
        return auth_info
