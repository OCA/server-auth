# © 2021 Florian Kantelberg - initOS GmbH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import _, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class VaultSendWizard(models.TransientModel):
    _name = "vault.send.wizard"
    _description = "Wizard to send another user a secret"

    user_id = fields.Many2one(
        "res.users",
        "User",
        required=True,
        domain=[("keys", "!=", False), ("inbox_enabled", "=", True)],
    )
    name = fields.Char(required=True)
    public = fields.Char(related="user_id.active_key.public")
    iv = fields.Char(required=True)
    key_user = fields.Char(required=True)
    key = fields.Char(required=True)
    secret = fields.Char()
    secret_file = fields.Char()
    filename = fields.Char()

    _sql_constraints = [
        (
            "value_check",
            "CHECK(secret IS NOT NULL OR secret_file IS NOT NULL)",
            "No value found",
        ),
    ]

    def action_send(self):
        if not self.secret and not self.secret_file:
            raise ValidationError(_("Neither a secret nor file was given"))

        self.ensure_one()
        self.env["vault.inbox"].sudo().create(
            {
                "name": self.name,
                "accesses": 0,
                "secret": self.secret,
                "secret_file": self.secret_file,
                "iv": self.iv,
                "key": self.key_user,
                "user_id": self.user_id.id,
                "filename": self.filename,
                "log_ids": [(0, 0, {"name": _("Created by %s") % self.user_id.name})],
            }
        )
