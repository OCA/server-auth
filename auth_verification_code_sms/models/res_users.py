# Copyright 2022 Akretion
# Copyright 2022 Toodigit
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, models


class ResUsers(models.Model):

    _inherit = "res.users"

    def _get_message_body_verifcode(self):
        return _("Your verification code for login is: {}")

    def send_verification_code_sms(self):
        message = self._get_message_body_verifcode().format(
            self.auth_verification_code_ids[-1].code_number
        )
        self.partner_id._message_sms(message)

    def _choose_verif_code_method(self):
        return "send_verification_code_sms"
