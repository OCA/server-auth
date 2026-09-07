# Copyright 2026 ForgeFlow S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import hmac
import logging
from hashlib import sha256

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class ResUsers(models.Model):
    _inherit = "res.users"

    auth_session_valid_from = fields.Datetime(
        string="Sessions Valid From",
        copy=False,
        readonly=True,
        help="Any browser session opened before this datetime is invalid: the "
        "user is redirected to the login page on their next request. The value "
        "is bumped by scheduled logout job and folded into the session token.",
    )

    def _compute_session_token(self, sid):
        token = super()._compute_session_token(sid)
        if not token:
            return token
        valid_from = self.sudo().auth_session_valid_from
        if valid_from:
            token_encoded = token.encode("utf-8")
            valid_from_encoded = valid_from.isoformat().encode("utf-8")
            encoded = hmac.new(token_encoded, valid_from_encoded, sha256)
            token = encoded.hexdigest()
        return token

    @api.model
    def _get_scheduled_logout_exempt_group(self):
        group_id = "auth_session_scheduled_logout.group_auth_session_no_sched_logout"
        group = self.env.ref(group_id, raise_if_not_found=False)
        return group or self.env["res.groups"]

    @api.model
    def _get_users_to_logout(self):
        domain = []
        exempt_group = self._get_scheduled_logout_exempt_group()
        if exempt_group:
            domain.append(("groups_id", "not in", exempt_group.ids))
        users = self.search(domain)
        tech_users = self.browse()
        for xmlid in ("base.public_user", "base.default_user"):
            if self.env.ref(xmlid, raise_if_not_found=False):
                tech_users |= self.env.ref(xmlid, raise_if_not_found=False)
        return users - tech_users

    @api.model
    def _cron_revoke_all_sessions(self):
        users = self._get_users_to_logout()
        if not users:
            return
        users.write({"auth_session_valid_from": fields.Datetime.now()})
        _logger.info("Scheduled logout: revoked sessions for %d user(s).", len(users))
