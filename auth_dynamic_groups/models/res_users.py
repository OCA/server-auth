# Copyright 2013-2019 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import SUPERUSER_ID, models
from odoo.api import Environment


class ResUsers(models.Model):
    _inherit = "res.users"

    @classmethod
    def _login(cls, db, login, password, user_agent_env):
        uid = super(ResUsers, cls)._login(db, login, password, user_agent_env)

        if uid and uid != SUPERUSER_ID:
            cls.update_dynamic_groups(uid, db)

        return uid

    @classmethod
    def update_dynamic_groups(cls, uid, db):
        with cls.pool.cursor() as cr:
            env = Environment(cr, SUPERUSER_ID, {})
            dynamic_groups = env["res.groups"].search([("is_dynamic", "=", True)])
            if dynamic_groups:
                cr.execute(
                    "delete from res_groups_users_rel " "where uid=%s and gid in %s",
                    (uid, tuple(dynamic_groups.ids)),
                )
            for dynamic_group in dynamic_groups:
                if dynamic_group.eval_dynamic_group_condition(uid=uid):
                    cr.execute(
                        "insert into res_groups_users_rel (uid, gid) values "
                        "(%s, %s)",
                        (uid, dynamic_group.id),
                    )
            env["res.users"].invalidate_cache(["groups_id"], [uid])
