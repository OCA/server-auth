# Copyright 2022 Akretion
# Copyright 2022 Toodigit
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import datetime
import logging
import random

from odoo import _, api, fields, models

from ..common import (
    DEFAULT_MAX_VERIF_CODE_ATTEMPTS,
    DEFAULT_MAX_VERIF_CODE_DELAY,
    DEFAULT_VERIF_CODE_EXPIRY,
    DEFAULT_VERIF_CODE_VALIDITY,
)

_logger = logging.getLogger(__name__)


class AuthVerificationCode(models.Model):
    _name = "auth.verification.code"
    _description = "Auth Verification Code"
    _order = "id"

    user_id = fields.Many2one("res.users")
    code_number = fields.Char()
    token = fields.Char()
    expiry_date = fields.Datetime(
        help="Date before which the code must be used, or become invalid"
    )
    validity_date = fields.Datetime(
        help="Date after which a new confirmation code must be generated and confirmed"
    )
    state = fields.Selection(
        [("confirmed", "Confirmed"), ("pending_confirmation", "Pending confirmation")],
        default="pending_confirmation",
    )
    log_ids = fields.One2many(
        "auth.verification.code.log", "auth_verification_code_ids"
    )

    def check_expired(self):
        return self.user_id.last_verif_code.expiry_date < datetime.datetime.now()

    def check_validity(self):
        return self.validity_date > datetime.datetime.now()

    def _generate_random_code(self):
        return random.randrange(100000, 999999)

    @api.model
    def create(self, vals):
        expiry_delay = int(
            self.env["ir.config_parameter"].get_param(
                "verification_code_expiry", default=DEFAULT_VERIF_CODE_EXPIRY
            )
        )
        validity_duration = int(
            self.env["ir.config_parameter"].get_param(
                "verification_code_validity", default=DEFAULT_VERIF_CODE_VALIDITY
            )
        )
        vals["expiry_date"] = datetime.datetime.now() + datetime.timedelta(
            minutes=int(expiry_delay)
        )
        vals["validity_date"] = datetime.datetime.now() + datetime.timedelta(
            minutes=int(validity_duration)
        )
        vals["code_number"] = self._generate_random_code()
        return super().create(vals)

    def action_confirm(self):
        for rec in self:
            rec.state = "confirmed"

    def verify(self, code_number):
        self.env["auth.verification.code.log"].create(
            {"auth_verification_code_ids": self.id}
        )
        max_code_attempts = int(
            self.env["ir.config_parameter"].get_param(
                "max_verif_code_attempts", default=DEFAULT_MAX_VERIF_CODE_ATTEMPTS
            )
        )
        max_code_attempts_delay = int(
            self.env["ir.config_parameter"].get_param(
                "max_verif_code_attempts_delay", default=DEFAULT_MAX_VERIF_CODE_DELAY
            )
        )
        date_floor = datetime.datetime.now() - datetime.timedelta(
            minutes=max_code_attempts_delay
        )
        verif_codes = self.log_ids.filtered(lambda r: r.create_date > date_floor)
        if len(verif_codes.ids) > max_code_attempts:
            return (_("Too many verification attempts, try again later"), False)
        elif code_number != self.code_number:
            return (_("Wrong verification code"), False)
        elif self.check_expired():
            # TODO eventually manage this case in a cleaner way
            return ("code expired", False)
        else:
            self.action_confirm()
            return ("", self.user_id)


class AuthVerificationCodeLog(models.Model):
    _name = "auth.verification.code.log"

    auth_verification_code_ids = fields.Many2one("auth.verification.code")
