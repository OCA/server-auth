# Copyright 2026 Kencove (https://www.kencove.com).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields

from .common import AuthExecuteAsTestCommon


class TestLogCleanup(AuthExecuteAsTestCommon):
    def test_log_cleanup_cron(self):
        """Test log cleanup cron job."""
        log = self.env["auth.api.log"].create(
            {
                "client_id": self.client.id,
                "model_name": "test",
                "method": "test",
                "status_code": 200,
            }
        )
        log.create_date = fields.Datetime.to_string(
            fields.Datetime.subtract(fields.Datetime.now(), days=31)
        )
        # Run cleanup with 30 days
        self.env["auth.api.log"]._cron_cleanup_old_logs(days=30)

        self.assertFalse(log.exists())

    def test_log_cleanup_keeps_recent(self):
        """Test that cleanup keeps recent logs."""
        log = self.env["auth.api.log"].create(
            {
                "client_id": self.client.id,
                "model_name": "test",
                "method": "test",
                "status_code": 200,
            }
        )

        # Run cleanup with 30 days
        self.env["auth.api.log"]._cron_cleanup_old_logs(days=30)

        self.assertTrue(log.exists())
