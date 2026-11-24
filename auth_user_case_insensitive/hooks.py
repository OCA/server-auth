# Copyright 2017 LasLabs Inc.
# Copyright 2021 Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo.exceptions import ValidationError


def pre_init_hook_login_check(env):
    """This hook will look to see if any conflicting logins exist before
    the module is installed
    :param env:
        Environment.
    """
    with env.cr.savepoint():
        users = []
        env.cr.execute("SELECT login FROM res_users")
        for user in env.cr.fetchall():
            login = user[0].lower()
            if login not in users:
                users.append(login)
            else:
                raise ValidationError(
                    env._("Conflicting user logins exist for `%s`", login)
                )


def post_init_hook_login_convert(env):
    """After the module is installed, set all logins to lowercase
    :param env:
        Environment.
    """
    with env.cr.savepoint():
        env.cr.execute("UPDATE res_users SET login=lower(login)")
