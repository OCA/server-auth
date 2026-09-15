# Copyright 2026 360ERP (<https://www.360erp.com>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)

import json
from datetime import timedelta
from uuid import uuid4

from odoo import fields, http
from odoo.tests import HttpCase, tagged

from odoo.addons.impersonate_login.models.impersonate_log import ACTIVITY_SESSION_KEY


@tagged("post_install", "-at_install")
class TestImpersonateLogEnd(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.log_model = cls.env["impersonate.log"]
        cls.admin_user = cls.env.ref("base.user_admin")
        group_impersonate = cls.env.ref("impersonate_login.group_impersonate_login")
        if group_impersonate not in cls.admin_user.group_ids:
            cls.admin_user.write(
                {"group_ids": [fields.Command.link(group_impersonate.id)]}
            )

        # A dedicated user to impersonate: demo data is not guaranteed, and the
        # password must be strong enough for password_security, which lands in
        # the same database on the CI.
        cls.target_login = "impersonate_target"
        Users = cls.env["res.users"].with_context(no_reset_password=True)
        cls.target_user = Users.search([("login", "=", cls.target_login)], limit=1)
        if not cls.target_user:
            cls.target_user = Users.create(
                {
                    "name": "Impersonation Target",
                    "login": cls.target_login,
                    "password": "Target!2345",
                    "group_ids": [
                        fields.Command.set([cls.env.ref("base.group_user").id])
                    ],
                }
            )

    # Helpers

    def _call_button(self, model, method, args):
        response = self.url_open(
            "/web/dataset/call_button",
            data=json.dumps(
                {
                    "params": {
                        "model": model,
                        "method": method,
                        "args": args,
                        "kwargs": {},
                    },
                }
            ),
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(response.status_code, 200)
        return response.json()

    def _impersonate_user(self, user):
        return self._call_button("res.users", "impersonate_login", [user.id])

    def _read_write_request(self):
        """Send a request served by a read/write cursor."""
        return self._call_button("res.users", "action_impersonate_login", [])

    def _get_session_info(self):
        """Send a request served by a readonly cursor."""
        response = self.url_open(
            "/web/session/get_session_info",
            data=json.dumps({"jsonrpc": "2.0", "method": "call", "id": str(uuid4())}),
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(response.status_code, 200)
        return response.json()

    def _logout(self):
        response = self.url_open("/web/session/logout", allow_redirects=False)
        self.assertEqual(response.status_code, 303)
        return response

    def _destroy_session(self):
        response = self.url_open(
            "/web/session/destroy",
            data=json.dumps({"jsonrpc": "2.0", "method": "call", "id": str(uuid4())}),
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(response.status_code, 200)
        return response.json()

    def _last_log(self):
        return self.log_model.search([], order="id desc", limit=1)

    def _new_log(self):
        return self.log_model.create(
            {
                "user_id": self.admin_user.id,
                "impersonated_partner_id": self.target_user.partner_id.id,
                "date_start": fields.Datetime.now(),
            }
        )

    def _set_write_date(self, log, value):
        """Move write_date in the past, which the ORM does not allow."""
        self.env.cr.execute(
            "UPDATE impersonate_log SET write_date = %s WHERE id = %s",
            (value, log.id),
        )
        log.invalidate_recordset()

    def _reset_activity_throttle(self):
        """Make the session believe its activity was never recorded."""
        session = http.root.session_store.get(self.session.sid)
        session[ACTIVITY_SESSION_KEY] = 0.0
        http.root.session_store.save(session)

    # Tests

    def test_10_logout_closes_the_log(self):
        """Logging out while impersonating closes the log"""
        self.authenticate(user="admin", password="admin")
        self._impersonate_user(self.target_user)

        log = self._last_log()
        self.assertEqual(log.user_id, self.admin_user)
        self.assertTrue(log.date_start)
        self.assertFalse(log.date_end)

        self._logout()

        log.invalidate_recordset()
        self.assertTrue(log.date_end)

    def test_20_destroy_session_closes_the_log(self):
        """Destroying the session while impersonating closes the log"""
        self.authenticate(user="admin", password="admin")
        self._impersonate_user(self.target_user)
        log = self._last_log()
        self.assertFalse(log.date_end)

        self._destroy_session()

        log.invalidate_recordset()
        self.assertTrue(log.date_end)

    def test_30_logout_without_impersonation(self):
        """Logging out without impersonating anybody does not touch any log"""
        self.authenticate(user="admin", password="admin")
        log = self._new_log()
        self.env.flush_all()

        self._logout()

        log.invalidate_recordset()
        self.assertFalse(log.date_end)

    def test_40_activity_is_recorded(self):
        """A read/write request of an impersonated session refreshes the activity"""
        self.authenticate(user="admin", password="admin")
        self._impersonate_user(self.target_user)
        log = self._last_log()

        past = fields.Datetime.now() - timedelta(hours=2)
        self._set_write_date(log, past)

        # Reset the throttle, otherwise the next request could be too close in
        # time to the previous one to trigger a write.
        self._reset_activity_throttle()
        self.env.flush_all()

        self._read_write_request()

        log.invalidate_recordset()
        self.assertGreater(log.write_date, past)
        self.assertFalse(log.date_end)

    def test_45_readonly_request_does_not_write(self):
        """A readonly request leaves the log untouched"""
        self.authenticate(user="admin", password="admin")
        self._impersonate_user(self.target_user)
        log = self._last_log()

        past = fields.Datetime.now() - timedelta(hours=2)
        self._set_write_date(log, past)
        self._reset_activity_throttle()
        self.env.flush_all()

        self._get_session_info()

        log.invalidate_recordset()
        self.assertEqual(log.write_date, past)

    def test_50_vacuum_closes_an_expired_log(self):
        """The vacuum closes a log whose session cannot be used anymore"""
        log = self._new_log()
        self.env.flush_all()
        max_inactivity = http.get_session_max_inactivity(self.env)
        long_ago = fields.Datetime.now() - timedelta(seconds=max_inactivity + 3600)
        self._set_write_date(log, long_ago)

        self.log_model._gc_expired_logs()

        self.assertEqual(log.date_end, long_ago)

    def test_60_vacuum_keeps_a_live_log_open(self):
        """The vacuum leaves a log with recent activity alone"""
        log = self._new_log()
        self.env.flush_all()

        self.log_model._gc_expired_logs()

        log.invalidate_recordset()
        self.assertFalse(log.date_end)
