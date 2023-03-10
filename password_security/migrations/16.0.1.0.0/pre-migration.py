# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

import logging

from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    if not version:
        return
    logger = logging.getLogger(__name__)
    logger.info(
        "Password Security: migration of the password_length "
        "value into standard minlength field."
    )
    env = api.Environment(cr, SUPERUSER_ID, {})
    if env["res.company"]._fields.get("password_length"):
        password_length_list = env["res.company"].search([]).mapped("password_length")
        ICP = env["ir.config_parameter"]
        minlength = ICP.get_param("auth_password_policy.minlength")
        minlength = int(minlength) if minlength else 0
        ICP.set_param(
            "auth_password_policy.minlength", max(minlength, *password_length_list)
        )
