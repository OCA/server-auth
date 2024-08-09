# Copyright 2019 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
import logging
import random
import string
from datetime import datetime, timedelta

from odoo import _, api, fields, http, models
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

    def __init__(self, pool, cr):
        super(ResUsers, self).__init__(pool, cr)
        type(self).SELF_WRITEABLE_FIELDS += ["auth_sms_enabled"]
        type(self).SELF_READABLE_FIELDS += ["auth_sms_enabled"]

    @api.constrains("auth_sms_enabled")
    def _check_auth_sms_enabled(self):
        for this in self:
            if this.auth_sms_enabled and not this.mobile:
                raise UserError(
                    _("User %s has no mobile phone number!") % this.login,
                )

    @api.model
    def check_credentials(self, password):
        super(ResUsers, self).check_credentials(password)
        self._auth_sms_check_credentials()

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
            raise AccessDeniedWrongSmsCode(_("Wong SMS code"))

    @api.model
    def _auth_sms_generate_code(self):
        """generate a code to send to the user for second factor"""
        choices = self.env["ir.config_parameter"].get_param(
            "auth_sms.code_chars",
            string.ascii_letters + string.digits,
        )
        return "".join(
            random.choice(choices)
            for dummy in range(
                int(
                    self.env["ir.config_parameter"].get_param(
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
        self.env["auth_sms.code"].create(
            {
                "code": code,
                "user_id": user.id,
                "session_id": request and request.session.sid,
            }
        )
        if not user._auth_sms_check_rate_limit():
            raise AccessDeniedSmsRateLimit(_("SMS rate limit"))
        if not self.env["sms.provider"].send_sms(user.mobile, code):
            raise UserError(_("Sending SMS failed"))

    @api.multi
    def _auth_sms_check_rate_limit(self):
        """return false if the user has requested an SMS code too often"""
        self.ensure_one()
        rate_limit_hours = float(
            self.env["ir.config_parameter"].get_param(
                "auth_sms.rate_limit_hours",
                24,
            )
        )
        rate_limit_limit = float(
            self.env["ir.config_parameter"].get_param(
                "auth_sms.rate_limit_limit",
                10,
            )
        )
        return (
            rate_limit_hours
            and rate_limit_limit
            and self.env["auth_sms.code"].search(
                [
                    (
                        "create_date",
                        ">=",
                        fields.Datetime.to_string(
                            datetime.now() - timedelta(hours=rate_limit_hours),
                        ),
                    ),
                    ("user_id", "=", self.id),
                ],
                count=True,
            )
            <= rate_limit_limit
        )

    @api.model_cr
    def _register_hook(self):
        # don't log our exceptions during RPC dispatch
        if AccessDeniedNoSmsCode not in http.NO_POSTMORTEM:
            http.NO_POSTMORTEM = tuple(
                list(http.NO_POSTMORTEM)
                + [
                    AccessDeniedNoSmsCode,
                    AccessDeniedWrongSmsCode,
                ],
            )
        return super(ResUsers, self)._register_hook()
