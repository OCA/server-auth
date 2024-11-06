# Copyright 2019-2025 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
import logging
import random
import string
from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.http import request

from ..exceptions import (
    AccessDeniedNoSmsCode,
    AccessDeniedSmsRateLimit,
    AccessDeniedWrongSmsCode,
)

_logger = logging.getLogger(__name__)


class ResUsers(models.Model):
    _inherit = "res.users"

    auth_sms_enabled = fields.Boolean(
        "Use SMS verification",
        help="Enable SMS authentication in addition to your password",
    )

    @property
    def SELF_WRITEABLE_FIELDS(self):
        return super().SELF_WRITEABLE_FIELDS + ["auth_sms_enabled"]

    @property
    def SELF_READABLE_FIELDS(self):
        return super().SELF_READABLE_FIELDS + ["auth_sms_enabled"]

    @api.constrains("auth_sms_enabled")
    def _check_auth_sms_enabled(self):
        for this in self:
            if this.auth_sms_enabled and not this.mobile:
                raise UserError(
                    _("User %s has no mobile phone number!") % this.login,
                )

    def _check_credentials(self, password, env):
        super()._check_credentials(password, env)
        return self._auth_sms_check_credentials()

    @api.model
    def _auth_sms_check_credentials(self):
        """if the user has enabled sms validation, check if we have the correct
        code in the session"""
        if not self.env.user.auth_sms_enabled:
            return
        code = request and request.session.get("auth_sms.code")
        if not code:
            raise AccessDeniedNoSmsCode(self.env.user, _("No SMS code"))
        if not self.env["auth_sms.code"].search(
            [
                ("code", "=", code),
                ("user_id", "=", self.id),
                ("session_id", "=", request.session.sid),
            ]
        ):
            raise AccessDeniedWrongSmsCode(_("Wrong SMS code"))

    @api.model
    def _auth_sms_generate_code(self):
        """generate a code to send to the user for second factor"""
        choices = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param(
                "auth_sms.code_chars",
                string.ascii_letters + string.digits,
            )
        )
        return "".join(
            random.choice(choices)
            for dummy in range(
                int(
                    self.env["ir.config_parameter"]
                    .sudo()
                    .get_param(
                        "auth_sms.code_length",
                        8,
                    ),
                )
            )
        )

    @api.model
    def _auth_sms_send(self, user_id):
        """send a code to the user for second factor, save this code with the
        session"""
        code = self._auth_sms_generate_code()
        _logger.debug(
            "using SMS code %s for session %s",
            code,
            request and request.session.sid,
        )
        user = self.env["res.users"].browse(user_id)
        self.env["auth_sms.code"].sudo().create(
            {
                "code": code,
                "user_id": user.id,
                "session_id": request and request.session.sid,
            }
        )
        if not user.sudo()._auth_sms_check_rate_limit():
            raise AccessDeniedSmsRateLimit(_("SMS rate limit"))
        mobile = user.sudo().mobile
        if not self.env["sms.provider"].send_sms(mobile, code):
            raise UserError(_("Sending SMS failed"))

    def _auth_sms_check_rate_limit(self):
        """Return false if the user has requested an SMS code too often"""
        self.ensure_one()
        rate_limit_hours = self._get_rate_limit_hours()
        rate_limit_limit = self._get_rate_limit_limit()
        if not (rate_limit_hours and rate_limit_limit):
            return False
        cutoff_time = fields.Datetime.now() - timedelta(hours=rate_limit_hours)
        already_sent = self.env["auth_sms.code"].search_count(
            [("create_date", ">=", cutoff_time), ("user_id", "=", self.id)]
        )
        within_limit = already_sent <= rate_limit_limit
        if not within_limit:
            _logger.info("To many sms's send to user %(login)s", {"login": self.login})
        return within_limit

    def _get_rate_limit_hours(self):
        """Return timeframe in which to check count of sms's send to user."""
        return float(
            self.env["ir.config_parameter"]
            .sudo()
            .get_param(
                "auth_sms.rate_limit_hours",
                24,
            )
        )

    def _get_rate_limit_limit(self):
        """Return limit of times sms send to user within a specific timeframe."""
        return float(
            self.env["ir.config_parameter"]
            .sudo()
            .get_param(
                "auth_sms.rate_limit_limit",
                10,
            )
        )

    def _mfa_type(self):
        """If auth_sms enabled, disable other totp methods."""
        sudo_self = self.sudo()
        result = super(ResUsers, sudo_self)._mfa_type()
        if len(self) != 1 or not sudo_self.auth_sms_enabled:
            return result
        # If we get here, we have one user record that is enabled for sms auth.
        return "auth_sms"
