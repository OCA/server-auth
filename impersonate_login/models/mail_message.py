# Copyright (C) 2024 Akretion (<http://www.akretion.com>).
# @author Kévin Roche <kevin.roche@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from markupsafe import Markup

from odoo import api, fields, models
from odoo.http import request


class Message(models.Model):
    _inherit = "mail.message"

    impersonated_author_id = fields.Many2one(
        comodel_name="res.partner",
        string="Impersonated By",
        readonly=True,
    )

    def _get_impersonate_notice(self):
        """Notice to prepend to a message body, or an empty string

        The notice names the user the message is written as, while the author
        of the message is the user actually behind the keyboard.
        """
        if not (request and request.session.get("impersonate_from_uid")):
            return ""
        effective_partner = self.env["res.users"].browse(request.session.uid).partner_id
        return Markup("<b>%s</b><br/>") % self.env._(
            "Logged in as %(name)s", name=effective_partner.name
        )

    def _add_impersonate_notice(self, vals, notice):
        """Prepend the notice to the body of ``vals``, at most once"""
        body = vals.get("body")
        if not body or str(body).startswith(notice):
            return vals
        return dict(vals, body=notice + Markup(body))

    @api.model_create_multi
    def create(self, vals_list):
        notice = self._get_impersonate_notice()
        if notice:
            impersonated_author_id = (
                self.env["res.users"]
                .browse(request.session.get("impersonate_from_uid"))
                .partner_id.id
            )
            vals_list = [
                dict(
                    self._add_impersonate_notice(vals, notice),
                    impersonated_author_id=impersonated_author_id,
                )
                for vals in vals_list
            ]
        return super().create(vals_list)

    def write(self, vals):
        # Keep the notice when a message is edited from an impersonated
        # session, but never rewrite the stamp of an existing message.
        if "body" in vals:
            notice = self._get_impersonate_notice()
            if notice:
                vals = self._add_impersonate_notice(vals, notice)
        return super().write(vals)
