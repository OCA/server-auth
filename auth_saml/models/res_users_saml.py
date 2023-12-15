# Copyright (C) 2022 XCG Consulting <https://xcg-consulting.fr/>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class ResUserSaml(models.Model):
    _name = "res.users.saml"
    _description = "User to SAML Provider Mapping"

    user_id = fields.Many2one("res.users", index=True, required=True)
    saml_provider_id = fields.Many2one(
        "auth.saml.provider", string="SAML Provider", index=True
    )
    saml_uid = fields.Char("SAML User ID", help="SAML Provider user_id", required=True)
    saml_access_token = fields.Char(
        "Current SAML token for this user",
        required=False,
        help="The current SAML token in use",
    )

    _sql_constraints = [
        (
            "uniq_users_saml_provider_saml_uid",
            "unique(saml_provider_id, saml_uid)",
            "SAML UID must be unique per provider",
        )
    ]

    @api.model_create_multi
    def create(self, vals_list):
        """Creates new records for the res.users.saml model"""
        # Redefined to remove password if necessary
        result = super().create(vals_list)
        if not self.env["res.users"].allow_saml_and_password():
            result.mapped("user_id").write({"password": False})
        return result
