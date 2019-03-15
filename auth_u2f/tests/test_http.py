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
from unittest.mock import patch

from odoo.exceptions import AccessDenied
from odoo.tests.common import TransactionCase
from ..models.http import U2FAuthenticationError
from .test_main import BASE_URL, REQUEST_DATA, RESPONSE_DATA


ADDON_PATH = 'odoo.addons.auth_u2f'
AUTH_PATH = 'odoo.addons.base.ir.ir_http.IrHttp._authenticate'
DEVICE_PATH = ADDON_PATH + '.models.u2f_device'
HTTP_PATH = ADDON_PATH + '.models.http'
USER_PATH = ADDON_PATH + '.models.res_users'


_logger = logging.getLogger(__name__)


@patch(HTTP_PATH + '.request')
class TestUsers(TransactionCase):

    @patch(DEVICE_PATH + '.request')
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

    def _authenticate(self, auth_method):
        return self.env['ir.http']._authenticate(auth_method)

    @patch(AUTH_PATH)
    def test_authenticate(self, super_mock, request_mock):
        request_mock.session.uid = self.test_user.id
        super_mock.return_value = 'U2F Test Ok'

        self.assertEqual(self._authenticate('user'), super_mock.return_value)

    @patch(AUTH_PATH)
    def test_authenticate_without_2nd_factor(self, super_mock, request_mock):
        request_mock.session.uid = self.test_user.id
        super_mock.return_value = 'U2F Test Ok'

        self.assertEqual(self._authenticate('none'), super_mock.return_value)

    @patch(AUTH_PATH)
    def test_authenticate_1st_factor_fail(self, super_mock, request_mock):
        request_mock.session.uid = self.test_user.id
        super_mock.side_effect = AccessDenied()

        try:
            self.env['ir.http']._authenticate()
        except AccessDenied:
            pass

    @patch(AUTH_PATH)
    @patch(USER_PATH + '.ResUsers.u2f_check_credentials')
    @patch(HTTP_PATH + '.api.Environment')
    def test_auth_2nd_fail(self, env_mock, check_mock, super_mock, req_mock):
        env_mock.return_value = self.env
        req_mock.session.uid = self.test_user.id
        check_mock.side_effect = U2FAuthenticationError()

        try:
            self._authenticate('user')
        except U2FAuthenticationError:
            pass

    @patch(AUTH_PATH)
    @patch(HTTP_PATH + '.api.Environment')
    def test_auth_no_device(self, env_mock, super_mock, request_mock):
        env_mock.return_value = self.env
        super_mock.return_value = 'U2F Test Ok'
        request_mock.session.uid = self.test_user.id

        self.device.unlink()

        self.assertEqual(self._authenticate('user'), super_mock.return_value)
