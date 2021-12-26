from odoo import _, api, fields, models, tools
from odoo.exceptions import ValidationError


class AuthJwtValidator(models.Model):
    _inherit = "auth.jwt.validator"

    user_id_strategy = fields.Selection(
        selection_add=[("login", "Login")],
        ondelete={'login': 'cascade'},
    )

    def _get_uid(self, payload):
        print(88)
        if self.user_id_strategy == 'login':
            if 'username' in payload and 'password' in payload:
                user = self.env['res.users'].search(
                    [
                        ("login", "=", payload['username'])
                    ]
                )
                if not user:
                    print('not user')
                    raise ValidationError
                user.with_user(user)._check_credentials(payload['password'], None)
                return user.id
            else:
                raise ValidationError
        else:
            return super()._get_uid(payload)
