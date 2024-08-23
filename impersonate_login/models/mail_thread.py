# Copyright (C) 2024 Akretion (<http://www.akretion.com>).
# @author Kévin Roche <kevin.roche@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models
from odoo.http import request


class MailThread(models.AbstractModel):
    _inherit = "mail.thread"

    def _message_compute_author(
        self, author_id=None, email_from=None, raise_on_email=True
    ):
        if request and request.session.impersonate_from_uid:
            author = self.env["res.users"].browse(request.session.uid).partner_id
            if author_id == author.id or author_id is None:
                impersonate_from_author = (
                    self.env["res.users"]
                    .browse(request.session.impersonate_from_uid)
                    .partner_id
                )
                email = impersonate_from_author.email_formatted
                return impersonate_from_author.id, email

        return super()._message_compute_author(
            author_id=author_id,
            email_from=email_from,
            raise_on_email=raise_on_email,
        )
