# Copyright 2014-2018 Laurent Mignon (ACSONE SA/NV)
# Copyright 2020 Dimitrios Tanis
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

import logging

from odoo.http import request
from odoo import models
from odoo.exceptions import AccessDenied


_logger = logging.getLogger(__name__)


class IrHttp(models.AbstractModel):
    _inherit = 'ir.http'

    @classmethod
    def _auth_method_basic(cls):
        if request.httprequest.authorization and not request.session.uid:
            uid = request.session.authenticate(
                request.session.db,
                request.httprequest.authorization.username,
                request.httprequest.authorization.password)
            if uid:
                return True
        _logger.error("Wrong HTTP BASIC Authentication, access denied")
        raise AccessDenied()
