# Copyright 2016 LasLabs Inc.
# Copyright 2017 Kaushal Prajapati <kbprajapati@live.com>.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    password_expiration = fields.Integer(
        'Days',
        default=60,
        help='How many days until passwords expire',
    )
    password_length = fields.Integer(
        'Characters',
        default=12,
        help='Minimum number of characters',
    )
    password_lower = fields.Integer(
        'Lowercase',
        default=1,
        help='Require number of lowercase letters',
    )
    password_upper = fields.Integer(
        'Uppercase',
        default=1,
        help='Require number of uppercase letters',
    )
    password_numeric = fields.Integer(
        'Numeric',
        default=1,
        help='Require number of numeric digits',
    )
    password_special = fields.Integer(
        'Special',
        default=1,
        help='Require number of unique special characters',
    )
    password_history = fields.Integer(
        'History',
        default=30,
        help='Disallow reuse of this many previous passwords - use negative '
             'number for infinite, or 0 to disable',
    )
    password_minimum = fields.Integer(
        'Minimum Hours',
        default=24,
        help='Amount of hours until a user may change password again',
    )
