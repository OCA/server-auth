# Copyright 2026 Kencove (https://www.kencove.com).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import timedelta

from odoo import api, fields, models


class AuthApiLog(models.Model):
    _name = "auth.api.log"
    _description = "API Log"
    _order = "create_date desc"

    client_id = fields.Many2one(
        "auth.api.client",
        string="Client",
        index=True,
    )
    user_id = fields.Many2one(
        "res.users",
        string="Impersonated User",
        index=True,
    )
    model_name = fields.Char(string="Model")
    method = fields.Char()
    request_payload = fields.Text()
    response_payload = fields.Text()
    status_code = fields.Integer()
    execution_time_ms = fields.Integer(string="Execution Time (ms)")
    request_size_bytes = fields.Integer(string="Request Size (bytes)")
    response_size_bytes = fields.Integer(string="Response Size (bytes)")

    @api.model
    def _cron_cleanup_old_logs(self, days=30):
        """Scheduled action to clean up old logs."""
        cutoff = fields.Datetime.now() - timedelta(days=days)
        old_logs = self.search([("create_date", "<=", cutoff)])
        old_logs.unlink()
        return True
