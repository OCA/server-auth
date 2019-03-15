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
from .test_main import BASE_URL, REQUEST_DATA, RESPONSE_DATA, TEST_VALUE
from odoo.addons.auth_u2f.models.http import U2FAuthenticationError


_logger = logging.getLogger(__name__)


MODELS_PATH = 'odoo.addons.auth_u2f.models'


class TestUsers(TransactionCase):

    @patch(MODELS_PATH + '.u2f_device.request')
    def setUp(self, request_mock):
        super(TestUsers, self).setUp()

        self.env['ir.config_parameter'].sudo().set_param(
            'web.base.url', BASE_URL)

        self.test_user = self.env.ref('base.user_root')

        request_mock.session.u2f_last_registration_challenge = REQUEST_DATA

        self.device = self.env['u2f.device'].create({
            'name': 'Test Authenticator',
            'json': json.dumps(RESPONSE_DATA),
            'user_id': self.test_user.id,
            'default': True,
        })

    @patch(MODELS_PATH + '.u2f_device.u2f')
    @patch(MODELS_PATH + '.u2f_device.request')
    def test_get_device(self, request_mock, u2f_mock):
        m = MagicMock(json=TEST_VALUE)
        u2f_mock.complete_registration.return_value = m, True

        device_b = self.env['u2f.device'].create({
            'name': 'Test Authenticator',
            'json': "Test",
            'user_id': self.test_user.id,
            'default': True,
        })

        devices = self.test_user._u2f_get_device()
        self.assertIn(device_b, devices)
        self.assertNotIn(self.device, devices)

    def test_get_device_no_default_device(self):
        self.device.default = False
        self.assertFalse(self.test_user._u2f_get_device())

    def test_get_device_no_device(self):
        self.device.unlink()
        self.assertFalse(self.test_user._u2f_get_device())

    @patch(MODELS_PATH + '.res_users.u2f')
    @patch(MODELS_PATH + '.res_users.request')
    def test_get_registration_challenge(self, request_mock, u2f_mock):
        m = MagicMock(json=TEST_VALUE)
        u2f_mock.begin_registration.return_value = m

        self.assertEqual(self.test_user.u2f_get_registration_challenge(), m)
        self.assertEqual(
            request_mock.session.u2f_last_registration_challenge, TEST_VALUE)

    @patch(MODELS_PATH + '.res_users.u2f')
    def test_get_login_challenge(self, u2f_mock):
        u2f_mock.begin_authentication.return_value = TEST_VALUE
        self.assertEqual(self.test_user._u2f_get_login_challenge(), TEST_VALUE)

        u2f_mock.begin_authentication.assert_called_once_with(
            BASE_URL, [self.device.json])

        self.device.default = False
        self.assertFalse(self.test_user._u2f_get_login_challenge())

    @patch(MODELS_PATH + '.res_users.u2f')
    def test_check_credentials_success(self, u2f_mock):
        u2f_mock.complete_authentication.return_value = True, True, True
        self.assertTrue(self.test_user.u2f_check_credentials(True, True))

    @patch(MODELS_PATH + '.res_users.u2f')
    def test_check_credentials_no_device(self, u2f_mock):
        self.device.default = False
        u2f_mock.complete_authentication.return_value = True, True, True
        self.assertTrue(self.test_user.u2f_check_credentials(True, True))

    @patch(MODELS_PATH + '.res_users.u2f')
    def test_check_credentials_missing_response(self, u2f_mock):
        u2f_mock.complete_authentication.return_value = True, True, True
        try:
            self.test_user.u2f_check_credentials(True, False)
            self.fail()
        except U2FAuthenticationError:
            pass

    @patch(MODELS_PATH + '.res_users.u2f')
    def test_check_credentials_missing_challenge(self, u2f_mock):
        u2f_mock.complete_authentication.return_value = True, True, True
        try:
            self.test_user.u2f_check_credentials(False, True)
            self.fail()
        except U2FAuthenticationError:
            pass

    @patch(MODELS_PATH + '.res_users.u2f')
    def test_check_credentials_fail(self, u2f_mock):
        u2f_mock.complete_authentication.return_value = False
        try:
            self.test_user.u2f_check_credentials(False, True)
            self.fail()
        except U2FAuthenticationError:
            pass
