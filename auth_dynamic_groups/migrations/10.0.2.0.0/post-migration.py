# -*- coding: utf-8 -*-
# Copyright 2019 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
# pylint: disable=missing-docstring,invalid-name,protected-access
# pylint: disable=unused-argument,broad-except
from odoo import registry


def migrate(cr, version=None):
    """Fill new fields."""
    # Update with separate cursor, to continue if anything fails...
    with registry(cr.dbname).cursor() as new_cr:
        try:
            new_cr.execute(
                "UPDATE res_groups SET group_type = 'formula'"
                " WHERE group_type = 'manual' AND is_dynamic")
            new_cr.commit()
        except Exception:
            pass
