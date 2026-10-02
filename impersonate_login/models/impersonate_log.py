# Copyright (C) 2024 Akretion (<http://www.akretion.com>).
# @author Kévin Roche <kevin.roche@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
import time
from datetime import timedelta

from odoo import SUPERUSER_ID, api, fields, models
from odoo.http import get_session_max_inactivity, request

_logger = logging.getLogger(__name__)

# Minimum delay, in seconds, between two touches of an open log. Low enough to
# keep the end date accurate, high enough to avoid a write on every request.
ACTIVITY_REFRESH_DELAY = 60

# Key used in the session to throttle those touches.
ACTIVITY_SESSION_KEY = "impersonate_activity_ts"


class ImpersonateLog(models.Model):
    _name = "impersonate.log"
    _description = "Impersonate Logs"

    user_id = fields.Many2one(
        comodel_name="res.users",
    )
    impersonated_partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Logged as",
    )
    date_start = fields.Datetime(
        string="Start Date",
    )
    date_end = fields.Datetime(
        string="End Date",
    )

    @api.model
    def _close_session_log(self):
        """Set the end date of the impersonation running in the current session.

        The logout route runs with ``auth="none"``, so the request may have no
        user at all. Writing as the superuser keeps the log writable in every
        case.
        """
        if not request or not request.session.impersonate_log_id:
            return
        log = (
            request.env(user=SUPERUSER_ID, su=True)["impersonate.log"]
            .browse(request.session.impersonate_log_id)
            .exists()
        )
        if log and not log.date_end:
            log.date_end = fields.Datetime.now()

    @api.model
    def _touch_session_log(self):
        """Record that the impersonation of the current session is still alive.

        Touching the log refreshes its ``write_date``, which is then used as
        the last known activity of the impersonation. Called on every request,
        but writes at most once every ``ACTIVITY_REFRESH_DELAY`` seconds.
        """
        session = request.session
        log_id = session.impersonate_log_id
        if not log_id:
            return
        if self.env.cr.readonly:
            # A readonly request cannot write. Skipping is on purpose: Odoo
            # would otherwise replay the whole request on a read/write cursor,
            # which is way too expensive for a heartbeat. The next read/write
            # request of the session refreshes the activity instead.
            return
        now = time.time()
        if now - (session.get(ACTIVITY_SESSION_KEY) or 0) < ACTIVITY_REFRESH_DELAY:
            return
        session[ACTIVITY_SESSION_KEY] = now
        request.env(user=SUPERUSER_ID, su=True)["impersonate.log"].browse(
            log_id
        ).exists().write({})

    @api.autovacuum
    def _gc_expired_logs(self):
        """Close the logs whose session can no longer be used.

        Odoo reaps a session that has been inactive for longer than
        ``sessions.max_inactivity_seconds``, so a log left open with no
        activity since then belongs to a session that is definitely gone. Its
        last activity is recorded as the end date, which is the closest we can
        get to the real end of the impersonation.

        This runs with the daily vacuum, next to the garbage collection of the
        sessions themselves.
        """
        threshold = fields.Datetime.now() - timedelta(
            seconds=get_session_max_inactivity(self.env)
        )
        logs = self.search([("date_end", "=", False), ("write_date", "<", threshold)])
        for log in logs:
            log.date_end = log.write_date
        if logs:
            _logger.info("Closed %s expired impersonate log(s).", len(logs))
        return len(logs)
