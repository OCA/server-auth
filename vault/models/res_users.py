# © 2021 Florian Kantelberg - initOS GmbH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
import re
from hashlib import sha256
from uuid import uuid4

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class ResUsers(models.Model):
    _inherit = "res.users"

    @api.depends("keys", "keys.current")
    def _compute_active_key(self):
        for rec in self:
            keys = rec.keys.filtered("current")
            rec.active_key = keys[0] if keys else None

    @api.depends("inbox_token")
    def _compute_inbox_link(self):
        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        for rec in self:
            rec.inbox_link = f"{base_url}/vault/inbox/{rec.inbox_token}"

    active_key = fields.Many2one(
        "res.users.key", compute=_compute_active_key, store=False,
    )
    keys = fields.One2many("res.users.key", "user_id", readonly=True)
    vault_right_ids = fields.One2many("vault.right", "user_id", readonly=True)
    inbox_enabled = fields.Boolean(default=True)
    inbox_link = fields.Char(compute=_compute_inbox_link, readonly=True, store=False)
    inbox_token = fields.Char(default=lambda self: uuid4(), readonly=True)

    @api.model
    def action_get_vault(self):
        return self.sudo().env.ref("vault.action_res_users_keys").read()[0]

    def action_new_share_token(self):
        self.ensure_one()
        self.inbox_token = uuid4()
        return {"type": "ir.actions.act_window_close"}

    @api.model
    def find_user_of_inbox(self, token):
        return self.search([("inbox_token", "=", token), ("inbox_enabled", "=", True)])

    def get_vault_keys(self):
        self.ensure_one()

        if not self.active_key:
            return {}

        return {
            "iterations": self.active_key.iterations,
            "iv": self.active_key.iv,
            "private": self.active_key.private,
            "public": self.active_key.public,
            "salt": self.active_key.salt,
            "uuid": self.active_key.uuid,
        }


class ResUsersKey(models.Model):
    _name = "res.users.key"
    _description = _("User data of a vault")
    _rec_name = "fingerprint"
    _order = "create_date DESC"

    @api.depends("public")
    def _compute_fingerprint(self):
        for rec in self:
            if rec.public:
                hashed = sha256(rec.public.encode()).hexdigest()
                rec.fingerprint = ":".join(re.findall(r".{2}", hashed))
            else:
                rec.fingerprint = False

    user_id = fields.Many2one("res.users", required=True)
    uuid = fields.Char(default=lambda self: uuid4(), required=True, readonly=True)
    current = fields.Boolean(default=True, readonly=True)
    fingerprint = fields.Char(compute=_compute_fingerprint, store=True)
    public = fields.Char(required=True, readonly=True)
    salt = fields.Char(required=True, readonly=True)
    iv = fields.Char(required=True, readonly=True)
    iterations = fields.Integer(required=True, readonly=True)
    # Encrypted with master password of user
    private = fields.Char(required=True, readonly=True)

    def store(self, iterations, iv, private, public, salt):
        if not all(isinstance(x, str) and x for x in [public, private, iv, salt]):
            raise ValidationError(_("Invalid parameter"))

        if not isinstance(iterations, int) or iterations < 4000:
            raise ValidationError(_("Invalid parameter"))

        domain = [
            ("user_id", "=", self.env.uid),
            ("private", "=", private),
        ]
        if not self.search(domain):
            # Disable all current keys
            self.env.user.keys.write({"current": False})

            rec = self.create(
                {
                    "iterations": iterations,
                    "iv": iv,
                    "private": private,
                    "public": public,
                    "salt": salt,
                    "user_id": self.env.uid,
                    "current": True,
                }
            )
            return rec.uuid
        return False

    def extract_public_key(self, user):
        user = self.sudo().search([("user_id", "=", user), ("current", "=", True)])
        return user.public or None
