# © 2021 Florian Kantelberg - initOS GmbH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import _, fields, models

_logger = logging.getLogger(__name__)


class VaultFile(models.Model):
    _name = "vault.file"
    _description = _("File of a vault")
    _order = "name"
    _inherit = ["vault.abstract.field", "vault.abstract"]

    value = fields.Binary(attachment=False)
