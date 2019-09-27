# -*- coding: utf-8 -*-
# Copyright 2019 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
import odoo
from odoo.addons.server_environment import serv_config

_logger = logging.Logger(__name__)


def migrate(cr, version):
    _logger.info("Create auth_api.key records from odoo config")
    with odoo.api.Environment.manage():
        env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})
        for section in serv_config.sections():
            if section.startswith("api_key_") and serv_config.has_option(
                section, "key"
            ):
                login_name = serv_config.get(section, "user")
                name = section.replace("api_key_", "")
                key = "<set from server environment>"
                user = env["res.users"].search([("login", "=", login_name)])
                env["auth.api.key"].create(
                    {"name": name, "key": key, "user_id": user.id}
                )
                _logger.info("API Key record created for %s", section)
