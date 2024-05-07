import hashlib
import logging

import requests

from odoo import _, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class ResUsers(models.Model):
    _inherit = "res.users"

    def _set_password(self):
        self._passwordshavebeenpwned(self.mapped("password"))

        return super()._set_password()

    def _passwordshavebeenpwned(self, passwords):
        for password in passwords:
            if self._passwordhasbeenpwned(password):
                raise UserError(
                    _("Password is already pwned and can no longer be used.")
                )

    def _passwordhasbeenpwned(self, password):
        params = self.env["ir.config_parameter"].sudo()
        api_url = params.get_param(
            "auth_password_pwned.range_url",
            default="https://api.pwnedpasswords.com/range/",
        )
        if api_url[-1] == "/":
            api_url = api_url[:-1]

        password_hash = hashlib.sha1(password.encode("utf-8")).hexdigest().upper()
        try:
            r = requests.get(
                "{api_url}/{hash}".format(api_url=api_url, hash=password_hash[:5]),
                headers={
                    "User-Agent": "Odoo OCA auth_password_pwned"
                    " https://github.com/OCA/server-auth",
                },
            )
            r.raise_for_status()
            response = r.text
            return password_hash[5:] in response
        except (
            requests.exceptions.HTTPError,
            requests.exceptions.RequestException,
        ) as error:
            if self.env.user.has_group("base.group_system"):
                # for admins display a message for them being able to fix the issue
                raise UserError(
                    _(f"{api_url} cannot be reached: {error}").format(api_url, error)
                ) from error
            else:
                # for other users log a warning
                _logger.warning(
                    _(f"{api_url} cannot be reached: {error}").format(api_url, error)
                )
                # and let them log into the system (if they have the correct password)
                return False
