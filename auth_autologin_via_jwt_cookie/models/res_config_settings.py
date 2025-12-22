# Copyright 2025 Kencove (https://www.kencove.com/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    auth_autologin_jwt_cookie_name = fields.Char(
        string="JWT Cookie Name",
        config_parameter="auth_autologin_via_jwt_cookie.jwt_cookie_name",
        help="Name of the shared cookie containing the JWT.",
    )
    auth_autologin_jwks_url = fields.Char(
        string="JWKS URL",
        config_parameter="auth_autologin_via_jwt_cookie.jwks_url",
        help="JWKS endpoint used to verify JWT signatures.",
    )
    auth_autologin_userinfo_url = fields.Char(
        string="Userinfo URL",
        config_parameter="auth_autologin_via_jwt_cookie.userinfo_url",
        help="Endpoint called with the JWT to retrieve the user email.",
    )
