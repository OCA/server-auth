# Copyright 2026 INVITU (<https://www.invitu.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    vault_portal_mfa_policy = fields.Selection(
        [
            ("none", "No constraint"),
            ("write", "Require 2FA for write/create access"),
            ("read", "Require 2FA for any portal access"),
        ],
        string="Portal contacts MFA policy",
        config_parameter="vault_portal.mfa_policy",
        default="none",
        help=(
            "No constraint: two-factor authentication is not required.\n"
            "Require 2FA for write/create access: a portal contact must "
            "have 2FA enabled before being granted write or create access "
            "to a vault; disabling 2FA afterwards downgrades their access "
            "back to read-only.\n"
            "Require 2FA for any portal access: a portal contact must have "
            "2FA enabled before being granted ANY access to a vault, "
            "including read-only; disabling 2FA afterwards immediately "
            "revokes all their vault access."
        ),
    )
