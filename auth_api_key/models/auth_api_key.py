# -*- coding: utf-8 -*-
# Copyright 2018 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models, tools, _

from odoo.addons.server_environment import serv_config

from odoo.exceptions import ValidationError, AccessError


class AuthApiKey(models.TransientModel):
    _name = "auth.api.key"

    @api.model
    @tools.ormcache("api_key")
    def _retrieve_uid_from_api_key(self, api_key):
        if not self.env.user.has_group("base.group_system"):
            raise AccessError(_("User is not allowed"))

        for section in serv_config.sections():
            if section.startswith("api_key_") and serv_config.has_option(
                    section, "key"
            ):
                if api_key != serv_config.get(section, "key"):
                    continue

                login_name = serv_config.get(section, "user")
                uid = self.env["res.users"].search(
                    [("login", "=", login_name)]).id

                if not uid:
                    raise ValidationError(
                        _("No user found with login %s") % login_name)

                return uid
        return False
