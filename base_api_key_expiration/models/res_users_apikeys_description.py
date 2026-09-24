# Copyright 2026 Camptocamp SA
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

import datetime

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class ResUsersApikeysDescription(models.TransientModel):
    # Backport of odoo/odoo#178558 (18.0)

    _inherit = "res.users.apikeys.description"

    def _selection_duration(self):
        # duration value is a string representing the number of days.
        durations = [
            ("1", "1 Day"),
            ("7", "1 Week"),
            ("30", "1 Month"),
            ("90", "3 Months"),
            ("180", "6 Months"),
            ("365", "1 Year"),
        ]
        persistent_duration = (
            "0",
            "Persistent Key",
        )  # Magic value to detect an infinite duration
        custom_duration = (
            "-1",
            "Custom Date",
        )  # Will force the user to enter a date manually
        if self.env.is_system():
            return durations + [persistent_duration, custom_duration]
        max_duration = (
            max(group.api_key_duration for group in self.env.user.groups_id) or 1.0
        )
        return list(
            filter(lambda duration: int(duration[0]) <= max_duration, durations)
        ) + [custom_duration]

    duration = fields.Selection(
        selection="_selection_duration",
        required=True,
        default=lambda self: self._selection_duration()[0][0],
    )
    expiration_date = fields.Datetime(
        compute="_compute_expiration_date",
        store=True,
        readonly=False,
    )

    @api.depends("duration")
    def _compute_expiration_date(self):
        for record in self:
            duration = int(record.duration)
            if duration >= 0:
                record.expiration_date = (
                    fields.Date.today() + datetime.timedelta(days=duration)
                    if int(record.duration)
                    else None
                )

    @api.onchange("expiration_date")
    def _onchange_expiration_date(self):
        try:
            self.env["res.users.apikeys"]._check_expiration_date(self.expiration_date)
        except UserError as error:
            warning = {
                "type": "notification",
                "title": _("The API key duration is not correct."),
                "message": error.args[0],
            }
            return {"warning": warning}

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        for description in res:
            self.env["res.users.apikeys"]._check_expiration_date(
                description.expiration_date
            )
        return res

    def make_key(self):
        return super(
            ResUsersApikeysDescription,
            self.with_context(api_key_expiration_date=self.expiration_date),
        ).make_key()
