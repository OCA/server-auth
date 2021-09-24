# Copyright 2021 Camptocamp SA
# @author: Simone Orsi <simone.orsi@camptocamp.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).


import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    if not version:
        return

    env = api.Environment(cr, SUPERUSER_ID, {})
    module = env["ir.module.module"].search(
        [("name", "=", "auth_api_key_server_env"), ("state", "=", "uninstalled")]
    )
    if module:
        module.write({"state": "to install"})
        _logger.info(
            "Install module auth_api_key_server_env to not break existing installations. "
            "If you don't want this module to be installed, uninstall it manually."
        )
    return
