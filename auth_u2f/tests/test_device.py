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

import json
import logging
from unittest.mock import MagicMock, patch

from odoo.tests.common import TransactionCase

from .test_main import REQUEST_DATA, RESPONSE_DATA, DEVICE_DATA, BASE_URL


_logger = logging.getLogger(__name__)


TEST_VALUE = "U2F Test Token"
MODEL_PATH = 'odoo.addons.auth_u2f.models.u2f_device'


class TestDevice(TransactionCase):

    def setUp(self):
        super(TestDevice, self).setUp()

        self.env['ir.config_parameter'].sudo().set_param(
            'web.base.url', BASE_URL)

        self.test_user = self.env.ref('base.user_root')

    @patch(MODEL_PATH + '.request')
    def test_create_device(self, request_mock):
        request_mock.session.u2f_last_registration_challenge = REQUEST_DATA

        device = self.env['u2f.device'].create({
            'name': 'Test Authenticator',
            'json': json.dumps(RESPONSE_DATA),
            'user_id': self.test_user.id,
            'default': True,
        })

        self.assertTrue(device)
        data = json.loads(device.json)

        for key, value in DEVICE_DATA.items():
            self.assertEqual(data[key], value, key)

    @patch(MODEL_PATH + '.u2f')
    @patch(MODEL_PATH + '.request')
    def test_make_default(self, request_mock, u2f_mock):
        m = MagicMock(json=TEST_VALUE)
        u2f_mock.complete_registration.return_value = m, True
        request_mock.session.u2f_last_registration_challenge = TEST_VALUE

        data = json.dumps(RESPONSE_DATA)
        device_a = self.env['u2f.device'].create({
            'name': 'Test Authenticator',
            'json': data,
            'user_id': self.test_user.id,
            'default': True,
        })

        u2f_mock.complete_registration.assert_called_once_with(
            TEST_VALUE, data, [BASE_URL])

        device_b = self.env['u2f.device'].create({
            'name': 'Test Authenticator',
            'json': json.dumps(RESPONSE_DATA),
            'user_id': self.test_user.id,
            'default': True,
        })

        self.assertFalse(device_a.default)
        self.assertTrue(device_b.default)

        device_a.action_make_default()
        self.assertTrue(device_a.default)
        self.assertFalse(device_b.default)
