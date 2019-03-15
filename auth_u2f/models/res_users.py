# Copyright (C) 2017 Joren Van Onder
# Copyright (C) 2019 initOS GmbH

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.

# You should have received a copy of the GNU Lesser General Public
# License along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301 USA

from odoo import api, fields, models
from odoo.http import request

import logging
from .http import U2FAuthenticationError

_logger = logging.getLogger(__name__)

try:
    import u2flib_server.u2f as u2f
except ImportError as err:
    _logger.debug(err)


class ResUsers(models.Model):
    _inherit = 'res.users'

    u2f_device_ids = fields.One2many(
        'u2f.device', 'user_id', string='U2F devices')

    @api.multi
    def _u2f_get_device(self):
        self.ensure_one()
        default_devices = self.u2f_device_ids.filtered('default')
        return default_devices[0] if default_devices else False

    @api.model
    def u2f_get_registration_challenge(self):
        user = self.env.user
        icp = self.env['ir.config_parameter'].sudo()
        baseurl = icp.get_param('web.base.url')
        already_registered_u2f_devices = user.u2f_device_ids.mapped('json')
        challenge = u2f.begin_registration(
            baseurl, already_registered_u2f_devices)
        request.session.u2f_last_registration_challenge = challenge.json

        return challenge

    @api.multi
    def _u2f_get_login_challenge(self):
        self.ensure_one()
        icp = self.env['ir.config_parameter'].sudo()
        baseurl = icp.get_param('web.base.url')
        devices = self._u2f_get_device()
        if devices:
            challenge = u2f.begin_authentication(baseurl, [devices.json])
            return challenge
        return False

    @api.multi
    def u2f_check_credentials(self, last_challenge, last_response):
        self.ensure_one()
        if self._u2f_get_device():
            icp = self.env['ir.config_parameter'].sudo()
            baseurl = icp.get_param('web.base.url')
            try:
                if last_challenge and last_response:
                    device, c, t = u2f.complete_authentication(
                        last_challenge, last_response, [baseurl])
                else:
                    raise U2FAuthenticationError()
            except Exception:
                _logger.info(
                    'Exception during U2F authentication.', exc_info=True)
                raise U2FAuthenticationError()

            _logger.debug('Successful U2F auth with: %s, %s, %s', device, c, t)
        return True
