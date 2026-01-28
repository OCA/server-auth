# Copyright 2026 Kencove (https://www.kencove.com).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AuthApiWhitelistLine(models.Model):
    _name = "auth.api.whitelist.line"
    _description = "API Whitelist Line"
    _rec_name = "display_name"

    whitelist_id = fields.Many2one(
        comodel_name="auth.api.whitelist",
        string="Whitelist",
        required=True,
        ondelete="cascade",
        index=True,
    )
    model_id = fields.Many2one(
        comodel_name="ir.model",
        string="Model",
        required=True,
        ondelete="cascade",
    )
    method = fields.Char(required=True)
    field_ids = fields.Many2many(
        comodel_name="ir.model.fields",
        relation="auth_api_whitelist_line_field_rel",
        column1="line_id",
        column2="field_id",
        string="Allowed Fields",
        domain="[('model_id', '=', model_id)]",
    )
    clean_response = fields.Boolean(
        default=True,
        help="""
        Clean response data:
            convert dates to ISO format, simplify Many2one (id, name) to just name
        """,
    )
    log_call = fields.Boolean(
        default=True,
        help="Log API calls for this method",
    )
    log_response = fields.Boolean(
        default=True,
        help="Include response payload in logs",
    )
    truncate_response = fields.Boolean(
        default=True,
        help="Truncate response payload to 10KB in logs",
    )
    display_name = fields.Char(
        compute="_compute_display_name",
        store=True,
    )

    @api.depends("model_id", "method")
    def _compute_display_name(self):
        for record in self:
            model_name = record.model_id.model if record.model_id else ""
            record.display_name = f"{model_name}.{record.method or ''}"
