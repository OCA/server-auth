# -*- coding: utf-8 -*-
# Copyright 2018 ACSONE SA/NV
# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import logging

from odoo.http import request
from odoo import models
from odoo.exceptions import AccessDenied


_logger = logging.getLogger(__name__)


class IrHttp(models.AbstractModel):
    _inherit = "ir.http"

    @classmethod
    def _auth_method_api_key(cls):
        headers = request.httprequest.environ
        api_key = headers.get("HTTP_API_KEY")
        if api_key:
            request.uid = 1
            uid = request.env["auth.api.key"]._retrieve_uid_from_api_key(
                api_key)
            if uid:
                # reset _env on the request since we change the uid...
                # the next call to env will instantiate an new
                # odoo.api.Environment with the user defined on the
                # auth.api_key
                request._env = None
                request.uid = uid
                request.auth_api_key = api_key
                return True
        _logger.error("Wrong HTTP_API_KEY, access denied")
        raise AccessDenied()
