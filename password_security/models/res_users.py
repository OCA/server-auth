# Copyright 2016 LasLabs Inc.
# Copyright 2017 Kaushal Prajapati <kbprajapati@live.com>.
# Copyright 2018 Modoolar <info@modoolar.com>.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

import logging
import re
from datetime import datetime, timedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)
try:
    import zxcvbn

    zxcvbn.feedback._ = _
except ImportError:
    _logger.debug(
        "Could not import zxcvbn. Please make sure this library is available"
        " in your environment."
    )


def delta_now(**kwargs):
    dt = datetime.now() + timedelta(**kwargs)
    return fields.Datetime.to_string(dt)


class ResUsers(models.Model):
    _inherit = "res.users"

    password_write_date = fields.Datetime(
        "Last password update", default=fields.Datetime.now, readonly=True
    )
    password_history_ids = fields.One2many(
        string="Password History",
        comodel_name="res.users.pass.history",
        inverse_name="user_id",
        readonly=True,
    )

    @api.model
    def create(self, vals):
        vals["password_write_date"] = fields.Datetime.now()
        return super(ResUsers, self).create(vals)

    def write(self, vals):
        if vals.get("password"):
            self._check_password(vals["password"])
            vals["password_write_date"] = fields.Datetime.now()
        return super(ResUsers, self).write(vals)

    @api.model
    def get_password_policy(self):
        data = super(ResUsers, self).get_password_policy()
        company_id = self.env.user.company_id
        if not company_id.password_policy_enabled:
            return data
        data.update(
            {
                "password_lower": company_id.password_lower,
                "password_upper": company_id.password_upper,
                "password_numeric": company_id.password_numeric,
                "password_special": company_id.password_special,
                "password_length": company_id.password_length,
                "password_estimate": company_id.password_estimate,
            }
        )
        return data

    def _check_password_policy(self, passwords):
        result = super(ResUsers, self)._check_password_policy(passwords)
        if not self.env.user.company_id.password_policy_enabled:
            return result
        for password in passwords:
            if not password:
                continue
            self._check_password(password)

        return result

    @api.model
    def get_estimation(self, password):
        return zxcvbn.zxcvbn(password)

    def password_match_message(self):
        self.ensure_one()
        company_id = self.company_id
        message = []
        if company_id.password_lower:
            message.append(
                _("\n* Lowercase letter (at least %s characters)")
                % str(company_id.password_lower)
            )
        if company_id.password_upper:
            message.append(
                _("\n* Uppercase letter (at least %s characters)")
                % str(company_id.password_upper)
            )
        if company_id.password_numeric:
            message.append(
                _("\n* Numeric digit (at least %s characters)")
                % str(company_id.password_numeric)
            )
        if company_id.password_special:
            message.append(
                _("\n* Special character (at least %s characters)")
                % str(company_id.password_special)
            )
        if message:
            message = [_("Must contain the following:")] + message
        if company_id.password_length:
            message = [
                _("Password must be %d characters or more.")
                % company_id.password_length
            ] + message
        return "\r".join(message)

    def _check_password(self, password):
        if not self.env.user.company_id.password_policy_enabled:
            return True
        self._check_password_rules(password)
        self._check_password_history(password)
        return True

    def _check_password_rules(self, password):
        self.ensure_one()
        if not password:
            return True
        company_id = self.company_id
        password_regex = [
            "^",
            "(?=.*?[a-z]){" + str(company_id.password_lower) + ",}",
            "(?=.*?[A-Z]){" + str(company_id.password_upper) + ",}",
            "(?=.*?\\d){" + str(company_id.password_numeric) + ",}",
            r"(?=.*?[\W_]){" + str(company_id.password_special) + ",}",
            ".{%d,}$" % int(company_id.password_length),
        ]
        if not re.search("".join(password_regex), password):
            raise ValidationError(self.password_match_message())

        estimation = self.get_estimation(password)
        if estimation["score"] < company_id.password_estimate:
            raise UserError(estimation["feedback"]["warning"])

        return True

    def _password_has_expired(self):
        self.ensure_one()
        if not self.company_id.password_policy_enabled:
            return False
        if not self.password_write_date:
            return True

        if not self.company_id.password_expiration:
            return False

        days = (fields.Datetime.now() - self.password_write_date).days
        return days > self.company_id.password_expiration

    def action_expire_password(self):
        expiration = delta_now(days=+1)
        for rec_id in self:
            rec_id.mapped("partner_id").signup_prepare(
                signup_type="reset", expiration=expiration
            )

    def _validate_pass_reset(self):
        """It provides validations before initiating a pass reset email
        :raises: UserError on invalidated pass reset attempt
        :return: True on allowed reset
        """
        for user in self:
            if not user.company_id.password_policy_enabled:
                continue
            pass_min = user.company_id.password_minimum
            if pass_min <= 0:
                continue
            write_date = user.password_write_date
            delta = timedelta(hours=pass_min)
            if write_date + delta > datetime.now():
                raise UserError(
                    _(
                        "Passwords can only be reset every %d hour(s). "
                        "Please contact an administrator for assistance."
                    )
                    % pass_min
                )
        return True

    def _check_password_history(self, password):
        """It validates proposed password against existing history
        :raises: UserError on reused password
        """
        crypt = self._crypt_context()
        for user in self:
            password_history = user.company_id.password_history
            if not password_history:  # disabled
                recent_passes = self.env["res.users.pass.history"].browse()
            elif password_history < 0:  # unlimited
                recent_passes = user.password_history_ids
            else:
                recent_passes = user.password_history_ids[:password_history]
            if recent_passes.filtered(
                lambda r: crypt.verify(password, r.password_crypt)
            ):
                raise UserError(
                    _("Cannot use the most recent %d passwords")
                    % user.company_id.password_history
                )

    def _set_encrypted_password(self, uid, pw):
        """It saves password crypt history for history rules"""
        res = super(ResUsers, self)._set_encrypted_password(uid, pw)
        if not self.env.user.company_id.password_policy_enabled:
            return res
        self.write({"password_history_ids": [(0, 0, {"password_crypt": pw})]})
        return res

    def action_reset_password(self):
        """Disallow password resets inside of Minimum Hours"""
        if not self.env.context.get("install_mode") and not self.env.context.get(
            "create_user"
        ):
            if not self.env.user._is_admin():
                users = self.filtered(lambda user: user.active)
                users._validate_pass_reset()
        return super().action_reset_password()
