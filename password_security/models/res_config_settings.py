# Copyright 2018 Modoolar <info@modoolar.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    # Imagine that the ir.config_parameter password_security.numeric has
    # a default value of 1. If the user sets the value to 0 on the config page,
    # the ir.config_parameter is deleted... but when the ir.config_parameter is not
    # present in the database, Odoo displays the default value
    # on the config page => Odoo displays 1 !
    # So, when the users sets the value of 0 on the config page, he will see 1
    # after saving the page !!!
    # If the default value is 0 (like auth_password_policy.minlength in the
    # module auth_password_policy of the official addons), there is no problem.
    # So the solution to avoid this problem and have a non-null default value:
    # 1) define the ir.config_parameter fields on res.config.settings with default=0
    # 2) initialize the ir.config_parameter with a default value in the init script
    # So the default value of the fields below are written in post_install.py
    password_expiration = fields.Integer(
        string="Days",
        default=0,
        config_parameter="password_security.expiration_days",
        help="How many days until passwords expire",
    )
    password_minimum = fields.Integer(
        string="Minimum Hours",
        default=0,
        config_parameter="password_security.minimum_hours",
        help="Number of hours until a user may change password again",
    )
    password_history = fields.Integer(
        string="History",
        default=0,
        config_parameter="password_security.history",
        help="Disallow reuse of this many previous passwords - use negative "
        "number for infinite, or 0 to disable",
    )
    password_lower = fields.Integer(
        string="Lowercase",
        default=0,
        config_parameter="password_security.lower",
        help="Require number of lowercase letters",
    )
    password_upper = fields.Integer(
        string="Uppercase",
        default=0,
        config_parameter="password_security.upper",
        help="Require number of uppercase letters",
    )
    password_numeric = fields.Integer(
        string="Numeric",
        default=0,
        config_parameter="password_security.numeric",
        help="Require number of numeric digits",
    )
    password_special = fields.Integer(
        string="Special",
        default=0,
        config_parameter="password_security.special",
        help="Require number of unique special characters",
    )
