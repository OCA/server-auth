# Copyright 2026 Lorenzo Battistini
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    oauth_server_issuer = fields.Char(
        string="OAuth Issuer URL",
        config_parameter="auth_oauth_server.issuer",
        help="Public address of this Odoo as applications reach it. Changing it "
        "invalidates every access token issued so far.",
    )
    oauth_server_cimd_enabled = fields.Boolean(
        string="Accept Client Metadata Documents",
        config_parameter="auth_oauth_server.cimd_enabled",
    )
    oauth_server_cimd_trusted_domains = fields.Char(
        string="Trusted Application Domains",
        config_parameter="auth_oauth_server.cimd_trusted_domains",
        help="Comma-separated domains whose metadata documents are accepted. "
        "Leave empty to accept any domain.",
    )
    oauth_server_dcr_enabled = fields.Boolean(
        string="Allow Dynamic Client Registration",
        config_parameter="auth_oauth_server.dcr_enabled",
    )

    def set_values(self):
        res = super().set_values()
        params = self.env["ir.config_parameter"].sudo()
        issuer = params.get_param("auth_oauth_server.issuer")
        if issuer and issuer != issuer.rstrip("/"):
            params.set_param("auth_oauth_server.issuer", issuer.rstrip("/"))
        resources = self.env["oauth.server.resource"].sudo()
        resources.with_context(active_test=False).search([])._sync_jwt_validator()
        return res
