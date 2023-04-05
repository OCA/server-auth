# Copyright 2023 Camptocamp SA
# @author: Simone Orsi <simone.orsi@camptocamp.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import logging

from odoo.tools import sql

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    # Stay backward compatible with having an active key for an archived user
    sql.create_column(cr, "auth_api_key", "active", "BOOLEAN")
    cr.execute("UPDATE auth_api_key set active=true;")
