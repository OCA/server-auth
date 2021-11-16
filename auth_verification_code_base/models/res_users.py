# Copyright 2022 Akretion
# Copyright 2022 Toodigit
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import datetime
import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from odoo.addons.auth_signup.models.res_partner import random_token

from ..common import TooManyVerifResendExc

ROLLING_DELAY_CODE_GENERATION_MINUTES = 15

_logger = logging.getLogger(__name__)


class ResUsers(models.Model):
    _inherit = "res.users"

    auth_verification_code_ids = fields.One2many("auth.verification.code", "user_id")
    verification_state = fields.Selection(
        [
            ("none", "None"),
            ("confirmed", "confirmed"),
            ("pending_confirmation", "Pending confirmation"),
        ],
        default="none",
        compute="_compute_verification_state",
        store=True,
    )

    @api.depends("auth_verification_code_ids.state")
    def _compute_verification_state(self):
        # use check_verification_state for expiry check
        for rec in self:
            rec.verification_state = (
                rec.auth_verification_code_ids
                and rec.auth_verification_code_ids[0].state
            ) or "none"

    def check_verification_state(self):
        if (
            self.auth_verification_code_ids
            and self.auth_verification_code_ids[-1]._check_expired()
        ):
            return "none"
        else:
            return self.verification_state

    def _generate_token(self):
        return random_token()

    def _check_verif_code_limit(self):
        delay = int(
            self.env["ir.config_parameter"].get_param("max_verif_code_generation_delay")
        )
        max_codes = int(
            self.env["ir.config_parameter"].get_param("max_verif_code_generation")
        )
        date_floor = datetime.datetime.now() - datetime.timedelta(minutes=delay)
        verif_codes = self.auth_verification_code_ids.filtered(
            lambda r: r.create_date > date_floor
        )
        if len(verif_codes.ids) > max_codes - 1:
            raise TooManyVerifResendExc

    def generate_verification_code(self):
        self._check_verif_code_limit()
        token = self._generate_token()
        new_verif_code = self.env["auth.verification.code"].create(
            {"user_id": self.id, "token": token}
        )
        self.send_verification_code(new_verif_code)
        return token

    def _choose_verif_code_method(self):
        return "send_verification_code_email"

    def send_verification_code(self, verif_code):
        sending_method = self._choose_verif_code_method()
        getattr(self, sending_method)()

    def send_verification_code_email(self):
        template = self.env.ref(
            "auth_verification_code_base.template_verification_code",
            raise_if_not_found=True,
        )
        if not self.email:
            raise UserError(
                _("Cannot send email: user %s has no email address.") % self.name
            )
        template.send_mail(self.id, force_send=True)

    @api.model
    def clear_unverified_users(self, delta_days):
        floor_date = fields.Datetime.to_string(
            datetime.datetime.now() - datetime.timedelta(days=delta_days)
        )
        unverified_users = self.env["res.users"].search(
            [("create_date", "<", floor_date)]
        )
        unverified_users -= unverified_users.filtered(lambda r: r.log_ids)
        unverified_users.unlink()
