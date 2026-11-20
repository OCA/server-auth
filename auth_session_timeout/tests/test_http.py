# Copyright 2026 Ecosoft Co., Ltd. (https://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import os
import time

from odoo.http.session import session_store
from odoo.tests import HttpCase, tagged

from ..models.ir_config_parameter import DELAY_KEY


@tagged("post_install", "-at_install")
class TestSessionTimeoutHttp(HttpCase):
    def setUp(self):
        super().setUp()
        self.env["ir.config_parameter"].set_int(DELAY_KEY, 60)
        self.authenticate("admin", "admin")

    def _age_session_file(self, seconds):
        path = session_store().get_session_path(self.session.sid)
        past = time.time() - seconds
        os.utime(path, (past, past))
        return path

    def test_active_session_kept(self):
        path = self._age_session_file(30)
        self.make_jsonrpc_request("/web/session/check")
        # activity refreshes the session file
        self.assertGreater(os.path.getmtime(path), time.time() - 30)

    def test_inactive_session_logged_out(self):
        self._age_session_file(120)
        res = self.url_open("/odoo", allow_redirects=False)
        self.assertEqual(res.status_code, 303)
        self.assertIn("/web/login", res.headers["Location"])
