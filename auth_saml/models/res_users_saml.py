from odoo import fields, models


class ResUserSaml(models.Model):
    _name = "res.users.saml"
    _description = "User to SAML Provider Mapping"

    user_id = fields.Many2one("res.users", index=True, required=True)
    saml_provider_id = fields.Many2one(
        "auth.saml.provider", string="SAML Provider", index=True
    )
    saml_uid = fields.Char("SAML User ID", help="SAML Provider user_id", required=True)

    _sql_constraints = [
        (
            "uniq_users_saml_provider_saml_uid",
            "unique(saml_provider_id, saml_uid)",
            "SAML UID must be unique per provider",
        )
    ]
