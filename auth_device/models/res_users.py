# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import exceptions, fields, models


class ResUsers(models.Model):
    _inherit = "res.users"
    _sql_constraints = [
        (
            "device_code_uniq",
            "UNIQUE(device_code)",
            "The device code should be unique.",
        )
    ]

    device_code = fields.Char("Device Code", copy=False)

    is_allowed_to_connect_with_device = fields.Boolean(
        string="Is allowed to connect with the external device?"
    )

    # pylint: disable=missing-return
    def _check_credentials(self, password, env):
        try:
            super()._check_credentials(password, env)

        except exceptions.AccessDenied:
            # Just be sure that parent methods aren't wrong
            user = (
                self.env["res.users"]
                .sudo()
                .search(
                    [
                        ("device_code", "=", password),
                        ("is_allowed_to_connect_with_device", "=", True),
                    ]
                )
            )
            if not user or len(user) > 1:
                raise
