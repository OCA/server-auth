# © 2021 Florian Kantelberg - initOS GmbH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import _, fields, models

_logger = logging.getLogger(__name__)


class VaultInboxLog(models.Model):
    _name = "vault.inbox.log"
    _description = _("Vault inbox log")
    _order = "create_date DESC"

    inbox_id = fields.Many2one(
        "vault.inbox",
        ondelete="cascade",
        readonly=True,
        required=True,
    )
    name = fields.Char(readonly=True)
