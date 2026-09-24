# Copyright 2026 Camptocamp SA
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo.tools import SQL


def post_init_hook(env):
    """Give the existing devices the expiration date of the new ones"""
    devices = env["auth_totp.device"]
    env.cr.execute(
        SQL(
            "UPDATE %s SET expiration_date = create_date + %s * INTERVAL '1 second'"
            " WHERE expiration_date IS NULL",
            SQL.identifier(devices._table),
            devices._get_trusted_device_age(),
        )
    )
