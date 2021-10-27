# © 2021 Florian Kantelberg - initOS GmbH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import _, fields, models

_logger = logging.getLogger(__name__)


class VaultShareLog(models.Model):
    _name = "vault.share.log"
    _description = _("Vault share log")
    _order = "create_date DESC"

    share_id = fields.Many2one(
        "vault.share",
        ondelete="cascade",
        readonly=True,
        required=True,
    )
    name = fields.Char(readonly=True)
