# Copyright 2023 Tecnativa - Carlos Roca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from openupgradelib import openupgrade


def set_users_key_version(env):
    openupgrade.logged_query(env.cr, "UPDATE res_users_key SET version = 1")


@openupgrade.migrate()
def migrate(env, version):
    set_users_key_version(env)
