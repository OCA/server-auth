# © 2021 Florian Kantelberg - initOS GmbH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
import re
from hashlib import sha256
from uuid import uuid4

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class ResUsersKey(models.Model):
    _name = "res.users.key"
    _description = "User data of a vault"
    _rec_name = "fingerprint"
    _order = "create_date DESC"

    user_id = fields.Many2one("res.users", required=True)
    uuid = fields.Char(default=lambda self: uuid4(), required=True, readonly=True)
    current = fields.Boolean(default=True, readonly=True)
    fingerprint = fields.Char(compute="_compute_fingerprint", store=True)
    public = fields.Char(required=True, readonly=True)
    salt = fields.Char(required=True, readonly=True)
    iv = fields.Char(required=True, readonly=True)
    iterations = fields.Integer(required=True, readonly=True)
    version = fields.Integer(readonly=True)
    # Encrypted with master password of user
    private = fields.Char(required=True, readonly=True)

    @api.depends("public")
    def _compute_fingerprint(self):
        for rec in self:
            if rec.public:
                hashed = sha256(rec.public.encode()).hexdigest()
                rec.fingerprint = ":".join(re.findall(r".{2}", hashed))
            else:
                rec.fingerprint = False

    def _prepare_values(self, iterations, iv, private, public, salt, version):
        return {
            "iterations": iterations,
            "iv": iv,
            "private": private,
            "public": public,
            "salt": salt,
            "user_id": self.env.uid,
            "current": True,
            "version": version,
        }

    def store(self, iterations, iv, private, public, salt, version):
        if not all(isinstance(x, str) and x for x in [public, private, iv, salt]):
            raise ValidationError(_("Invalid parameter"))

        if not isinstance(iterations, int) or iterations < 4000:
            raise ValidationError(_("Invalid parameter"))

        if not isinstance(version, int):
            raise ValidationError(_("Invalid parameter"))

        domain = [
            ("user_id", "=", self.env.uid),
            ("private", "=", private),
        ]
        key = self.search(domain)
        if not key:
            # Disable all current keys
            self.env.user.keys.write({"current": False})

            rec = self.create(
                self._prepare_values(iterations, iv, private, public, salt, version)
            )
            return rec.uuid

        return False

    def extract_public_key(self, user):
        user = self.sudo().search([("user_id", "=", user), ("current", "=", True)])
        return user.public or None
