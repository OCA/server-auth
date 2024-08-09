# Copyright 2019 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
import logging

import requests

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class SmsProvider(models.Model):
    """Provide fields for API keys or similar, and implement actually sending
    SMS via the provider selected in field `provider` by implementing the
    function `_send_sms_$provider`. This function is called on the record of
    the configured provider, and supposed to return a truthy value if the SMS
    is sent, and a falsy value otherwise"""

    # this class is a little overengineerd for the purpose at hand, but this
    # could be the preparation for a module base_sms that doesn't rely on
    # Odoo's in app purchases as the v12 sms module does
    _name = "sms.provider"
    _description = "Holds whatever data necessary to send an SMS via some "
    "provider"
    _rec_name = "provider"
    _order = "sequence desc"

    active = fields.Boolean(default=True)
    sequence = fields.Integer()
    provider = fields.Selection(
        [("messagebird", "MessageBird")],
        required=True,
    )
    api_key = fields.Char()

    @api.multi
    def action_send_test(self):
        for this in self:
            this.send_sms(self.env.user.mobile, "test")

    @api.model
    def send_sms(self, number, text, **kwargs):
        provider = self.search([], limit=1)
        if not provider:
            return False

        _logger.debug(
            "attempting to send SMS %s to %s via %s",
            text,
            number,
            provider.provider,
        )
        return getattr(
            provider,
            "_send_sms_%s" % provider.provider,
            lambda x: False,
        )(number, text, **kwargs)

    @api.multi
    def _send_sms_messagebird(self, number, text, **kwargs):
        self.ensure_one()
        result = requests.post(
            "https://rest.messagebird.com/messages",
            headers={
                "Authorization": "AccessKey %s" % self.api_key,
            },
            data={
                "originator": self.env.user.company_id.phone
                or self.env.user.company_id.name[:11],
                "recipients": number,
                "body": text,
            },
        ).json()
        _logger.debug(result)
        if result.get("errors"):
            return False
        return result
