# Copyright 2016 LasLabs Inc.
# Copyright 2017 Kaushal Prajapati <kbprajapati@live.com>.
# Copyright 2018 Modoolar <info@modoolar.com>.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

import re
from datetime import datetime, timedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


def delta_now(**kwargs):
    return datetime.now() + timedelta(**kwargs)


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

    def write(self, vals):
        if vals.get("password"):
            vals["password_write_date"] = fields.Datetime.now()
        return super().write(vals)

    @api.model
    def _get_all_password_params(self):
        params = self.env["ir.config_parameter"].sudo()
        res = {
            "minlength": int(
                params.get_param("auth_password_policy.minlength", default=0)
            ),
            "expiration_days": int(
                params.get_param("password_security.expiration_days", default=60)
            ),
            "minimum_hours": int(
                params.get_param("password_security.minimum_hours", default=60)
            ),
            "history": int(params.get_param("password_security.history", default=30)),
            "lower": int(params.get_param("password_security.lower", default=1)),
            "upper": int(params.get_param("password_security.upper", default=1)),
            "numeric": int(params.get_param("password_security.numeric", default=1)),
            "special": int(params.get_param("password_security.special", default=1)),
        }
        return res

    @api.model
    def get_password_policy(self):
        data = super().get_password_policy()
        pwd_params = self._get_all_password_params()
        data.update(
            {
                "password_lower": pwd_params["lower"],
                "password_upper": pwd_params["upper"],
                "password_numeric": pwd_params["numeric"],
                "password_special": pwd_params["special"],
            }
        )
        return data

    def _check_password_policy(self, passwords):
        result = super()._check_password_policy(passwords)

        for password in passwords:
            if not password:
                continue
            self._check_password(password)

        return result

    def password_match_message(self):
        self.ensure_one()
        message = []
        pwd_params = self._get_all_password_params()
        if pwd_params["lower"]:
            message.append(
                _("\n* Lowercase letter (at least %s characters)") % pwd_params["lower"]
            )
        if pwd_params["upper"]:
            message.append(
                _("\n* Uppercase letter (at least %s characters)") % pwd_params["upper"]
            )
        if pwd_params["numeric"]:
            message.append(
                _("\n* Numeric digit (at least %s characters)") % pwd_params["numeric"]
            )
        if pwd_params["special"]:
            message.append(
                _("\n* Special character (at least %s characters)")
                % pwd_params["special"]
            )
        if message:
            message = [_("Must contain the following:")] + message

        if pwd_params["minlength"]:
            message = [
                _("Password must be %d characters or more.") % pwd_params["minlength"]
            ] + message
        return "\r".join(message)

    def _check_password(self, password):
        self._check_password_rules(password)
        self._check_password_history(password)
        return True

    def _check_password_rules(self, password):
        self.ensure_one()
        if not password:
            return True
        pwd_params = self._get_all_password_params()
        password_regex = [
            "^",
            "(?=.*?[a-z]){" + str(pwd_params["lower"]) + ",}",
            "(?=.*?[A-Z]){" + str(pwd_params["upper"]) + ",}",
            "(?=.*?\\d){" + str(pwd_params["numeric"]) + ",}",
            r"(?=.*?[\W_]){" + str(pwd_params["special"]) + ",}",
            ".{%d,}$" % pwd_params["minlength"],
        ]
        if not re.search("".join(password_regex), password):
            raise ValidationError(self.password_match_message())

        return True

    def _password_has_expired(self):
        self.ensure_one()
        if not self.password_write_date:
            return True

        pwd_params = self._get_all_password_params()
        if not pwd_params["expiration_days"]:
            return False

        days = (fields.Datetime.now() - self.password_write_date).days
        return days > pwd_params["expiration_days"]

    def action_expire_password(self):
        for user in self:
            user.mapped("partner_id").signup_prepare(signup_type="reset")

    def _validate_pass_reset(self):
        """It provides validations before initiating a pass reset email
        :raises: UserError on invalidated pass reset attempt
        :return: True on allowed reset
        """
        pwd_params = self._get_all_password_params()
        for user in self:
            if pwd_params["minimum_hours"] <= 0:
                continue
            write_date = user.password_write_date
            delta = timedelta(hours=pwd_params["minimum_hours"])
            if write_date + delta > datetime.now():
                raise UserError(
                    _(
                        "Passwords can only be reset every %d hour(s). "
                        "Please contact an administrator for assistance."
                    )
                    % pwd_params["minimum_hours"]
                )
        return True

    def _check_password_history(self, password):
        """It validates proposed password against existing history
        :raises: UserError on reused password
        """
        crypt = self._crypt_context()
        pwd_params = self._get_all_password_params()
        for user in self:
            if not pwd_params["history"]:  # disabled
                recent_passes = self.env["res.users.pass.history"]
            elif pwd_params["history"] < 0:  # unlimited
                recent_passes = user.password_history_ids
            else:
                recent_passes = user.password_history_ids[: pwd_params["history"]]
            if recent_passes.filtered(
                lambda r: crypt.verify(password, r.password_crypt)
            ):
                raise UserError(
                    _("Cannot use the most recent %d passwords") % pwd_params["history"]
                )

    def _set_encrypted_password(self, uid, pw):
        """It saves password crypt history for history rules"""
        res = super()._set_encrypted_password(uid, pw)

        self.env["res.users.pass.history"].create(
            {
                "user_id": uid,
                "password_crypt": pw,
            }
        )
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
