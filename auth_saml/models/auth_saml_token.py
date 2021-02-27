from odoo import fields, models


class SamlToken(models.Model):
    _name = "auth_saml.token"
    _description = "SAML Token"
    _rec_name = "user_id"

    saml_provider_id = fields.Many2one(
        "auth.saml.provider",
        string="SAML Provider that issued the token",
        required=True,
    )
    user_id = fields.Many2one(
        "res.users",
        required=True,
        # we want the token to be destroyed if the corresponding res.users
        # is deleted
        ondelete="cascade",
        index=True,
    )
    saml_access_token = fields.Char(
        "Current SAML token for this user",
        required=True,
        help="The current SAML token in use",
    )
