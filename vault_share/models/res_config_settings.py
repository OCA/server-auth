# © 2021 Florian Kantelberg - initOS GmbH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    vault_share_delay = fields.Integer(
        string="Delayed Deletion",
        related="company_id.vault_share_delay",
        readonly=False,
        help="Delays the deletion of a share. After the expiration date it continues "
        "to stay inaccessible",
    )

    @api.onchange("vault_share_delay")
    def _onchange_vault_share_delay(self):
        self.vault_share_delay = max(0, self.vault_share_delay)
