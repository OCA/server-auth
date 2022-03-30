# Copyright 2016 LasLabs Inc.
# Copyright 2017 Kaushal Prajapati <kbprajapati@live.com>.
# Copyright 2018 Modoolar <info@modoolar.com>.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

import logging
import re
from datetime import datetime, timedelta

from odoo import _, api, fields, models

from ..exceptions import PassError

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
        "Last password update", default=fields.Datetime.now, readonly=True,
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

        for password in passwords:
            if not password:
                continue
            self._check_password(password)

        return result

    @api.model
    def get_estimation(self, password):
        msg_translate = {
            "Use a few words, avoid common phrases.": _(
                "Use a few words, avoid common phrases."
            ),
            "No need for symbols, digits, or uppercase letters.": _(
                "No need for symbols, digits, or uppercase letters."
            ),
            "Add another word or two. Uncommon words are better.": _(
                "Add another word or two. Uncommon words are better."
            ),
            "Straight rows of keys are easy to guess.": _(
                "Straight rows of keys are easy to guess."
            ),
            "Short keyboard patterns are easy to guess.": _(
                "Short keyboard patterns are easy to guess."
            ),
            "Use a longer keyboard pattern with more turns.": _(
                "Use a longer keyboard pattern with more turns."
            ),
            'Repeats like "aaa" are easy to guess.': _(
                'Repeats like "aaa" are easy to guess.'
            ),
            'Repeats like "abcabcabc" are only slightly harder to guess than "abc".': _(
                'Repeats like "abcabcabc" are only slightly harder  to guess than '
                '"abc".'
            ),
            "Avoid repeated words and characters.": _(
                "Avoid repeated words and characters."
            ),
            'Sequences like "abc" or "6543" are easy to guess.': _(
                'Sequences like "abc" or "6543" are easy to guess.'
            ),
            "Avoid sequences.": _("Avoid sequences."),
            "Recent years are easy to guess.": _("Recent years are easy to guess."),
            "Avoid recent years.": _("Avoid recent years."),
            "Avoid years that are associated with you.": _(
                "Avoid years that are associated with you."
            ),
            "Dates are often easy to guess.": _("Dates are often easy to guess."),
            "Avoid dates and years that are associated with you.": _(
                "Avoid dates and years that are associated with you."
            ),
            "This is a top-10 common password.": _("This is a top-10 common password."),
            "This is a top-100 common password.": _(
                "This is a top-100 common password."
            ),
            "This is a very common password.": _("This is a very common password."),
            "This is similar to a commonly used password.": _(
                "This is similar to a commonly used password."
            ),
            "A word by itself is easy to guess.": _(
                "A word by itself is easy to guess."
            ),
            "Names and surnames by themselves are easy to guess.": _(
                "Names and surnames by themselves are easy to guess."
            ),
            "Common names and surnames are easy to guess.": _(
                "Common names and surnames are easy to guess."
            ),
            "Capitalization doesn't help very much.": _(
                "Capitalization doesn't help very much."
            ),
            "All-uppercase is almost as easy to guess as all-lowercase.": _(
                "All-uppercase is almost as easy to guess as all-lowercase."
            ),
            "Reversed words aren't much harder to guess.": _(
                "Reversed words aren't much harder to guess."
            ),
            "Predictable substitutions like '@' instead of 'a' don't help very much.": _(
                "Predictable substitutions like '@' instead of 'a' don't help very "
                "much."
            ),
        }
        estimation = zxcvbn.zxcvbn(password)
        warning = estimation["feedback"]["warning"]
        suggestions = estimation["feedback"]["suggestions"]
        if warning in msg_translate:
            estimation["feedback"]["warning"] = msg_translate[warning]
        translated_suggestions = []
        for suggestion in suggestions:
            translated_suggestions.append(
                msg_translate[suggestion] if suggestion in msg_translate else suggestion
            )
        estimation["feedback"]["suggestions"] = translated_suggestions
        return estimation

    def password_match_message(self):
        self.ensure_one()
        company_id = self.company_id
        message = []
        if company_id.password_lower:
            if company_id.password_lower > 1:
                message.append(
                    "\n* "
                    + _(
                        "Lowercase letter (At least %(password_lower_config)d "
                        "characters)"
                    )
                    % dict(password_lower_config=company_id.password_lower)
                )
            else:
                message.append(
                    "\n* "
                    + _(
                        "Lowercase letter (At least %(password_lower_config)d "
                        "character)"
                    )
                    % dict(password_lower_config=company_id.password_lower)
                )
        if company_id.password_upper:
            if company_id.password_upper > 1:
                message.append(
                    "\n* "
                    + _(
                        "Uppercase letter (At least %(password_upper_config)d "
                        "characters)"
                    )
                    % dict(password_upper_config=company_id.password_upper)
                )
            else:
                message.append(
                    "\n* "
                    + _(
                        "Uppercase letter (At least %(password_upper_config)d "
                        "character)"
                    )
                    % dict(password_upper_config=company_id.password_upper)
                )
        if company_id.password_numeric:
            if company_id.password_numeric > 1:
                message.append(
                    "\n* "
                    + _(
                        "Numeric digit (At least %(password_numeric_config)d "
                        "characters)"
                    )
                    % dict(password_numeric_config=company_id.password_numeric)
                )
            else:
                message.append(
                    "\n* "
                    + _(
                        "Numeric digit (At least %(password_numeric_config)d "
                        "character)"
                    )
                    % dict(password_numeric_config=company_id.password_numeric)
                )
            if company_id.password_special:
                if company_id.password_special > 1:
                    message.append(
                        "\n* "
                        + _(
                            "Special character (At least %(password_special_config)d "
                            "characters)"
                        )
                        % dict(password_special_config=company_id.password_special)
                    )
                else:
                    message.append(
                        "\n* "
                        + _(
                            "Special character (At least %(password_special_config)d "
                            "character)"
                        )
                        % dict(password_special_config=company_id.password_special)
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
            raise PassError(self.password_match_message())

        estimation = self.get_estimation(password)
        if estimation["score"] < company_id.password_estimate:
            suggestions = estimation["feedback"]["suggestions"]
            full_msg = estimation["feedback"]["warning"] + "\n"
            if suggestions:
                full_msg += _("Suggestion(s) :\n")
                for suggestion in suggestions:
                    full_msg += suggestion
            raise PassError(full_msg)

        return True

    def _password_has_expired(self):
        self.ensure_one()
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
        :raises: PassError on invalidated pass reset attempt
        :return: True on allowed reset
        """
        for rec_id in self:
            pass_min = rec_id.company_id.password_minimum
            if pass_min <= 0:
                pass
            write_date = rec_id.password_write_date
            delta = timedelta(hours=pass_min)
            if write_date + delta > datetime.now():
                raise PassError(
                    _(
                        "Passwords can only be reset every %d hour(s). "
                        "Please contact an administrator for assistance."
                    )
                    % pass_min,
                )
        return True

    def _check_password_history(self, password):
        """It validates proposed password against existing history
        :raises: PassError on reused password
        """
        crypt = self._crypt_context()
        for rec_id in self:
            recent_passes = rec_id.company_id.password_history
            if recent_passes < 0:
                recent_passes = rec_id.password_history_ids
            else:
                recent_passes = rec_id.password_history_ids[0 : recent_passes - 1]
            if recent_passes.filtered(
                lambda r: crypt.verify(password, r.password_crypt)
            ):
                raise PassError(
                    _("Cannot use the most recent %d passwords")
                    % rec_id.company_id.password_history
                )

    def _set_encrypted_password(self, uid, pw):
        """ It saves password crypt history for history rules """
        super(ResUsers, self)._set_encrypted_password(uid, pw)

        self.write({"password_history_ids": [(0, 0, {"password_crypt": pw})]})
