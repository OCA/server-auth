# Copyright 2024 Akretion (http://www.akretion.com).
# @author Florian Mounier <florian.mounier@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import requests

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class CrossConnectServer(models.Model):
    _name = "cross.connect.server"
    _description = "Cross Connect Server"
    _inherit = "server.env.mixin"

    name = fields.Char(
        required=True,
        help="This name will be used for the new created app",
    )
    server_url = fields.Char(required=True)
    api_key = fields.Char(
        required=True,
    )
    group_ids = fields.One2many(
        "res.groups",
        inverse_name="cross_connect_server_id",
        string="Cross Connect Server Groups",
        readonly=True,
    )
    menu_id = fields.Many2one(
        "ir.ui.menu",
        string="Menu",
        help="Menu to display the Cross Connect Server in the menu",
        compute="_compute_menu_id",
        store=True,
    )
    web_icon_data = fields.Binary(
        compute="_compute_web_icon_data", inverse="_inverse_web_icon_data"
    )

    @api.depends("name", "group_ids")
    def _compute_menu_id(self):
        for record in self:
            if not record.group_ids:
                if record.menu_id:
                    if record.menu_id.action:
                        record.menu_id.action.unlink()
                    record.menu_id.unlink()
                record.menu_id = False
                continue

            menu_groups = record.group_ids

            if not record.menu_id:
                action = self.env["ir.actions.act_url"].create(
                    {
                        "name": record.name,
                        "url": f"/cross_connect_server/{record.id}",
                        "target": "new",
                    }
                )

                record.menu_id = self.env["ir.ui.menu"].create(
                    {
                        "name": record.name,
                        "action": f"ir.actions.act_url,{action.id}",  # noqa
                        "web_icon": "cross_connect_client,static/description/web_icon_data.png",
                        "groups_id": [(6, 0, menu_groups.ids)],
                        "sequence": 100,
                    }
                )
            else:
                record.menu_id.name = record.name
                record.menu_id.groups_id = [(6, 0, menu_groups.ids)]

    @api.depends("menu_id")
    def _compute_web_icon_data(self):
        for record in self:
            record.web_icon_data = record.menu_id.web_icon_data

    def _inverse_web_icon_data(self):
        for record in self:
            record.menu_id.web_icon_data = record.web_icon_data

    def _absolute_url_for(self, path):
        return f"{self.server_url.rstrip('/')}/cross_connect/{path.lstrip('/')}"

    def _request(self, method, url, headers=None, data=None):
        headers = headers or {}
        headers["api-key"] = self.api_key
        response = requests.request(
            method,
            self._absolute_url_for(url),
            headers=headers,
            json=data,
            timeout=10,
        )
        response.raise_for_status()
        return response.json()

    def _get_cross_connect_url(self, redirect_url=None):
        self.ensure_one()
        groups = self.env.user.groups_id & self.group_ids
        if not groups:
            raise UserError(_("You are not allowed to access this server"))

        if not self.env.user.email:
            raise UserError(_("User email is required"))

        data = {
            "id": self.env.user.id,
            "name": self.env.user.name,
            "login": self.env.user.login,
            "email": self.env.user.email,
            "lang": self.env.user.lang,
            "groups": [group.cross_connect_server_group_id for group in groups],
        }
        if redirect_url:
            data["redirect_url"] = redirect_url

        response = self._request("POST", "/access", data=data)
        client_id = response.get("client_id")
        token = response.get("token")
        if not token:
            raise UserError(_("Missing token"))

        return self._absolute_url_for(f"login/{client_id}/{token}")

    def _sync_groups(self):
        self.ensure_one()
        response = self._request("GET", "/sync")
        remote_groups = response.get("groups", [])
        # Removing groups that are not on the remote server
        remote_groups_ids = {remote_group["id"] for remote_group in remote_groups}
        self.group_ids.filtered(
            lambda group: group.cross_connect_server_group_id not in remote_groups_ids
        ).write({"cross_connect_server_id": False})

        # Create or Update existing groups
        for remote_group in remote_groups:
            existing_group = self.env["res.groups"].search(
                [("cross_connect_server_group_id", "=", remote_group["id"])]
            )
            if existing_group and not existing_group.cross_connect_server_id:
                existing_group.write({"cross_connect_server_id": self.id})
            if existing_group:
                existing_group.sudo().write(
                    {
                        "name": f"{self.name}: {remote_group['name']}",
                        "comment": remote_group["comment"],
                    }
                )
            else:
                self.env["res.groups"].sudo().create(
                    {
                        "cross_connect_server_id": self.id,
                        "cross_connect_server_group_id": remote_group["id"],
                        "name": f"{self.name}: {remote_group['name']}",
                        "comment": remote_group["comment"],
                    }
                )

    def action_sync(self):
        for record in self:
            record._sync_groups()

    def action_disable(self):
        for record in self:
            record.group_ids.write({"cross_connect_server_id": False})

    @property
    def _server_env_fields(self):
        return {"api_key": {}}

    def unlink(self):
        for rec in self:
            # deleting the groups will delete the menu and related action.
            rec.group_ids.unlink()
        return super().unlink()
