# Copyright 2023 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    archived_user_disable_auth_api_key = fields.Boolean(
        string="Disable API key for archived user",
        help=(
            "If checked, when a user is archived/unactivated the same change is "
            "propagated to his related api key. It is not retroactive (nothing is done "
            " when enabling/disabling this option)."
        ),
    )
