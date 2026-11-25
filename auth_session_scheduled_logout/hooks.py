# Copyright 2026 ForgeFlow S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from datetime import datetime, time, timedelta

from odoo import fields

_logger = logging.getLogger(__name__)


def post_init_hook(env):
    # Schedule the first run at the next Sunday 23:00 (UTC)
    cron = env.ref("auth_session_scheduled_logout.cron_revoke_all_sessions")
    if not cron:
        return
    now = fields.Datetime.now()
    ahead = (6 - now.weekday()) % 7
    next_call = datetime.combine(now.date() + timedelta(days=ahead), time(23, 0))
    if next_call <= now:
        next_call += timedelta(days=7)
    cron.nextcall = next_call
    _logger.info("Scheduled first session logout for %s UTC.", next_call)
