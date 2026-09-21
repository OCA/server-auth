# Copyright 2018 Therp BV <https://therp.nl>
# Copyright 2018 Brainbean Apps <https://brainbeanapps.com>
# Copyright 2026 Invitu <https://www.invitu.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import SUPERUSER_ID, api, models


class ResUsers(models.Model):
    _inherit = "res.users"

    @classmethod
    def _login(cls, db, credential, user_agent_env):
        auth_info = super()._login(db, credential, user_agent_env)
        if not auth_info:
            return auth_info
        with cls.pool.cursor() as cr:
            login = credential["login"]
            env = api.Environment(cr, SUPERUSER_ID, {})
            user = env["res.users"].browse(auth_info["uid"])
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
