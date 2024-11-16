# Copyright 2024 Akretion France (https://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

# to understand why we created this init script, read the comment
# in res_config_settings.py
def init_config_parameters(env):
    defaultvalues = {
        "password_security.expiration_days": 60,
        "password_security.minimum_hours": 24,
        "password_security.history": 30,
        "password_security.lower": 1,
        "password_security.upper": 1,
        "password_security.numeric": 1,
        "password_security.special": 1,
    }
    for key, value in defaultvalues.items():
        env["ir.config_parameter"].set_param(key, value)
