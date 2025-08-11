# Copyright 2018 Therp BV <https://therp.nl>
# Copyright 2018 Brainbean Apps <https://brainbeanapps.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import SUPERUSER_ID, api, models, registry


class ResUsers(models.Model):
    _inherit = "res.users"

    @classmethod
    def _login(cls, db, login, password, user_agent_env):
        user_id = super()._login(db, login, password, user_agent_env)
        if not user_id:
            return user_id
        with registry(db).cursor() as cr:
            env = api.Environment(cr, SUPERUSER_ID, {})
            user = env["res.users"].browse(user_id)
            # check if this user came from ldap, rerun get_or_create_user in
            # this case to apply ldap groups if necessary
            ldaps = user.company_id.ldaps
            if user.active and any(ldaps.mapped("only_ldap_groups")):
                for conf in ldaps._get_ldap_dicts():
                    entry = ldaps._authenticate(conf, login, password)
                    if entry:
                        ldaps._get_or_create_user(conf, login, entry)
                        break
        return user_id
