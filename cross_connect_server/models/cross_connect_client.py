# Copyright 2024 Akretion (http://www.akretion.com).
# @author Florian Mounier <florian.mounier@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from datetime import datetime, timedelta, timezone
from secrets import token_urlsafe

import jwt

from odoo import _, api, fields, models
from odoo.exceptions import AccessDenied


class CrossConnectClient(models.Model):
    _name = "cross.connect.client"
    _description = "Cross Connect Client"
    _inherit = "server.env.mixin"

    name = fields.Char(required=True)

    endpoint_id = fields.Many2one(
        "fastapi.endpoint",
        required=True,
        string="Endpoint",
    )

    api_key = fields.Char(
        required=True,
        string="API Key",
        help="The API key to give to configure on the client.",
        default=lambda self: self._generate_api_key(),
    )

    allowed_group_ids = fields.Many2many(
        related="endpoint_id.cross_connect_allowed_group_ids",
    )

    group_ids = fields.Many2many(
        "res.groups",
        string="Groups",
        help="The groups that this client belongs to.",
        domain="[('id', 'in', allowed_group_ids)]",
    )

    user_ids = fields.One2many(
        "res.users",
        "cross_connect_client_id",
        string="Users",
        help="The users created by this cross connection.",
    )
    user_count = fields.Integer(
        compute="_compute_user_count",
        string="Cross Connected User Count",
        help="The number of users created by this cross connection.",
    )

    @api.model
    def _generate_api_key(self):
        # generate random ~64 chars secret key
        return token_urlsafe(64)

    @api.depends("user_ids")
    def _compute_user_count(self):
        for record in self:
            record.user_count = len(record.user_ids)

    def _request_access(self, access_request):
        # check groups
        groups = self.env["res.groups"].browse(access_request.groups)
        if groups - self.group_ids or not groups.exists():
            raise AccessDenied(_("You are not allowed to access this endpoint."))

        user = self.user_ids.filtered(
            lambda u: u.cross_connect_client_user_id == access_request.id
        )
        vals = {
            "login": f"{self.id}_{access_request.id}_{access_request.login}",
            "email": access_request.email,
            "name": access_request.name,
            "lang": access_request.lang,
            "groups_id": [(6, 0, groups.ids)],
            "cross_connect_client_id": self.id,
            "cross_connect_client_user_id": access_request.id,
        }
        # Create user if not exists
        if not user:
            user = (
                self.env["res.users"].with_context(no_reset_password=True).create(vals)
            )
        else:
            user.write(vals)

        return jwt.encode(
            {
                "exp": datetime.now(tz=timezone.utc) + timedelta(minutes=2),
                "aud": str(self.id),
                "id": user.id,
                "redirect_url": access_request.redirect_url or "/web",
            },
            self.endpoint_id.cross_connect_secret_key,
            algorithm="HS256",
        )

    def _log_from_token(self, token):
        try:
            obj = jwt.decode(
                token,
                self.endpoint_id.cross_connect_secret_key,
                audience=str(self.id),
                options={"require": ["exp", "aud", "id"]},
                algorithms=["HS256"],
            )
        except jwt.PyJWTError as e:
            raise AccessDenied(_("Invalid Token")) from e

        user = self.env["res.users"].browse(obj["id"])

        if not user:
            raise AccessDenied(_("Invalid Token"))

        return user, obj["redirect_url"]
