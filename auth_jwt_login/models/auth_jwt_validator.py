import time

import werkzeug

from odoo import _, fields, models
from odoo.exceptions import ValidationError


class AuthJwtValidator(models.Model):
    _inherit = "auth.jwt.validator"

    user_id_strategy = fields.Selection(
        selection_add=[("login", "Login")],
        ondelete={"login": "cascade"},
    )

    def _get_uid(self, payload):
        if self.user_id_strategy == "login":
            timestamp_expiration_date = payload["exp"]
            if timestamp_expiration_date:
                timestamp_now = int(time.time())
                if (timestamp_expiration_date - timestamp_now) < 0:
                    raise werkzeug.exceptions.Forbidden(_("Token not valid."))
            if "username" in payload:
                user = self.env["res.users"].search(
                    [("login", "=", payload["username"])]
                )
                if not user:
                    raise ValidationError
                return user.id
            else:
                raise ValidationError
        else:
            return super()._get_uid(payload)
