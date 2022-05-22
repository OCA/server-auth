# © 2021 Florian Kantelberg - initOS GmbH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from datetime import datetime, timedelta
from uuid import uuid4

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)


class VaultShare(models.Model):
    _name = "vault.share"
    _description = _("Vault share outgoing secrets")

    user_id = fields.Many2one("res.users", default=lambda self: self.env.uid)
    name = fields.Char(required=True)
    share_link = fields.Char(
        "Share URL",
        compute="_compute_url",
        store=False,
        help="Using this link and pin people can access the secret.",
    )
    token = fields.Char(readonly=True, required=True, default=lambda self: uuid4())
    secret = fields.Char()
    secret_file = fields.Char()
    filename = fields.Char()
    salt = fields.Char(required=True)
    iv = fields.Char(required=True)
    pin = fields.Char(required=True, help="The pin needed to decrypt the share.")
    accesses = fields.Integer(
        "Access counter",
        default=5,
        help="Specifies how often a share can be accessed before deletion.",
    )
    expiration = fields.Datetime(
        default=lambda self: datetime.now() + timedelta(days=7),
        help="Specifies how long a share can be accessed until deletion.",
    )

    _sql_constraints = [
        (
            "value_check",
            "CHECK(secret IS NOT NULL OR secret_file IS NOT NULL)",
            _("No value found"),
        ),
    ]

    @api.depends("token")
    def _compute_url(self):
        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        for rec in self:
            rec.share_link = f"{base_url}/vault/share/{rec.token}"

    @api.model
    def get(self, token):
        rec = self.search([("token", "=", token)], limit=1)
        if not rec:
            return rec

        if datetime.now() < rec.expiration and rec.accesses > 0:
            rec.accesses -= 1
            return rec

        rec.unlink()
        return None

    @api.model
    def clean(self):
        now = datetime.now()
        self.search([("expiration", "<=", now), ("accesses", "<=", 0)]).unlink()
