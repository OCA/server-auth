# Copyright 2024 Akretion France (http://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    env.cr.execute(
        f"SELECT {openupgrade.get_legacy_name('password_expiration')}, "
        f"{openupgrade.get_legacy_name('password_minimum')}, "
        f"{openupgrade.get_legacy_name('password_history')}, "
        f"{openupgrade.get_legacy_name('password_lower')}, "
        f"{openupgrade.get_legacy_name('password_upper')}, "
        f"{openupgrade.get_legacy_name('password_numeric')}, "
        f"{openupgrade.get_legacy_name('password_special')} "
        "FROM res_company WHERE active is true ORDER BY id LIMIT 1"
    )
    res = env.cr.fetchone()
    env["ir.config_parameter"].set_param("password_security.expiration_days", res[0])
    env["ir.config_parameter"].set_param("password_security.minimum_hours", res[1])
    env["ir.config_parameter"].set_param("password_security.history", res[2])
    env["ir.config_parameter"].set_param("password_security.lower", res[3])
    env["ir.config_parameter"].set_param("password_security.upper", res[4])
    env["ir.config_parameter"].set_param("password_security.numeric", res[5])
    env["ir.config_parameter"].set_param("password_security.special", res[6])
