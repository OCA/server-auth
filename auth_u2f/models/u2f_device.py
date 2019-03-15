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

import logging

from odoo import api, fields, models
from odoo.http import request

_logger = logging.getLogger(__name__)

try:
    import u2flib_server.u2f as u2f
except ImportError as err:
    _logger.debug(err)


class U2FDevice(models.Model):
    _name = 'u2f.device'

    name = fields.Char(required=True)
    json = fields.Char(
        string='Scan', required=True,
        help='Technical data returned by u2flib or the browser'
    )
    user_id = fields.Many2one(
        'res.users', required=True, readonly=True,
        default=lambda self: self.env.uid
    )
    default = fields.Boolean(help='Device used during login.', readonly=True)

    @api.model
    def create(self, vals):
        res = super(U2FDevice, self).create(vals)
        res._register_device()
        res.action_make_default()
        return res

    @api.multi
    def _register_device(self):
        icp = self.env['ir.config_parameter'].sudo()
        baseurl = icp.get_param('web.base.url')
        for device in self:
            registration_data, cert = u2f.complete_registration(
                request.session.u2f_last_registration_challenge,
                device.json,
                [baseurl])
            device.json = registration_data.json
            del request.session['u2f_last_registration_challenge']

        return True

    @api.multi
    def action_make_default(self):
        self.ensure_one()
        self.user_id.u2f_device_ids.write({'default': False})
        self.default = True

        return True
