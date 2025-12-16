# © 2021 Florian Kantelberg - initOS GmbH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from datetime import datetime, timedelta
from uuid import uuid4

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class VaultShare(models.Model):
    _name = "vault.share"
    _description = "Vault share outgoing secrets"

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
    iterations = fields.Integer()
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
    log_ids = fields.One2many("vault.share.log", "share_id", "Log", readonly=True)

    _sql_constraints = [
        (
            "value_check",
            "CHECK(secret IS NOT NULL OR secret_file IS NOT NULL)",
            "No value found",
        ),
    ]

    @api.depends("token")
    def _compute_url(self):
        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        for rec in self:
            rec.share_link = f"{base_url}/vault/share/{rec.token}"

    @api.model
    def get(self, token, ip=None):
        rec = self.search([("token", "=", token)], limit=1)
        if not rec:
            return rec

        if datetime.now() < rec.expiration and rec.accesses > 0:
            rec.accesses -= 1
            log = self.env._("The share was accessed by %(name)s via %(ip)s")
            rec.log_ids = [
                (0, 0, {"name": log % {"name": self.env.user.name, "ip": ip or "n/a"}})
            ]
            return rec

        return None

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        log = self.env._("The share was created by %(name)s")
        for rec in res:
            rec.log_ids = [(0, 0, {"name": log % {"name": self.env.user.name}})]
        return res

    @api.model
    def clean(self):
        now = datetime.now()
        offset = timedelta(days=self.env.company.vault_share_delay)
        self.search([("expiration", "<=", now + offset)]).unlink()
