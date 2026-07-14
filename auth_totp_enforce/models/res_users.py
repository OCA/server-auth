# Copyright 2026 ForgeFlow S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
import functools
import logging
import os
import re

from odoo import models
from odoo.http import request

from odoo.addons.auth_totp.models.totp import TOTP, TOTP_SECRET_SIZE

_logger = logging.getLogger(__name__)

compress = functools.partial(re.sub, r"\s", "")


class ResUsers(models.Model):
    _inherit = "res.users"

    def _mfa_enforced(self):
        self.ensure_one()
        user = self.sudo()
        exempt_group = "auth_totp_enforce.group_mfa_exempt"
        return user._is_internal() and not user.has_group(exempt_group)

    def _mfa_url(self):
        r = super()._mfa_url()
        if r is not None:
            return r
        if self._mfa_enforced() and not self.totp_enabled:
            return "/web/login/totp/setup"

    def _generate_totp_setup_secret(self):
        secret = base64.b32encode(os.urandom(TOTP_SECRET_SIZE // 8)).decode()
        return " ".join(map("".join, zip(*[iter(secret)] * 4, strict=False)))

    def _totp_enforce_setup(self, secret, code):
        self.ensure_one()
        assert self.env.su or (
            request
            and not request.session.uid
            and request.session.get("pre_uid") == self.id
        ), "Only callable for the user currently in the pre-authentication phase"
        secret = compress(secret).upper()
        try:
            code = int(compress(str(code)))
        except ValueError:
            return False
        if TOTP(base64.b32decode(secret)).match(code) is None:
            _logger.info("2FA enforce setup: REJECT CODE for %r", self.login)
            return False
        self.sudo().totp_secret = secret
        _logger.info("2FA enforce setup: SUCCESS for %r", self.login)
        return True
