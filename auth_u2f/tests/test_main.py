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
import unittest.mock as mock

from odoo.exceptions import AccessDenied
from odoo.addons.auth_u2f.controllers.main import AuthU2FController, U2FLogin
from odoo.addons.auth_u2f.models.http import U2FAuthenticationError
from odoo.tests.common import TransactionCase


REQUEST_DATA = {
    'appId': 'http://localhost',
    'registeredKeys': [],
    'registerRequests': [{
        'challenge': u'ro-1pJjGqG8IjsaavEON7enhuBRLVsGpA6uMIc6Vle4',
        'version': 'U2F_V2'
    }],
}

RESPONSE_DATA = {
    'version': 'U2F_V2',
    'registrationData':
        u'BQRFVDpgpafxroN_Rt7FcRQN8LbBLujnd9iayp-UKkT1tvIJhFefSb9GQHkOFd2yj49'
        u'IsHA3JHWTutW_GwD49NwrQI_ccuvlvKzKdVkuxLCH2FjWPnHVx2nKtt7EEt4aibTwLi'
        u'hepxbkxTzIl-VWmcXrwiZlvkNyjb0gHyXbSJ7JdSUwggGHMIIBLqADAgECAgkAmb7os'
        u'Qyi7BwwCQYHKoZIzj0EATAhMR8wHQYDVQQDDBZZdWJpY28gVTJGIFNvZnQgRGV2aWNl'
        u'MB4XDTEzMDcxNzE0MjEwM1oXDTE2MDcxNjE0MjEwM1owITEfMB0GA1UEAwwWWXViaWN'
        u'vIFUyRiBTb2Z0IERldmljZTBZMBMGByqGSM49AgEGCCqGSM49AwEHA0IABDvhl91zfp'
        u'g9n7DeCedcQ8gGXUnemiXoi-JEAxz-EIhkVsMPAyzhtJZ4V3CqMZ-MOUgICt2aMxacM'
        u'X9cIa8dgS2jUDBOMB0GA1UdDgQWBBQNqL-TV04iaO6mS5tjGE6ShfexnjAfBgNVHSME'
        u'GDAWgBQNqL-TV04iaO6mS5tjGE6ShfexnjAMBgNVHRMEBTADAQH_MAkGByqGSM49BAE'
        u'DSAAwRQIgXJWZdbvOWdhVaG7IJtn44o21Kmi8EHsDk4cAfnZ0r38CIQD6ZPi3Pl4lXx'
        u'bY7BXFyrpkiOvCpdyNdLLYbSTbvIBQOTBFAiA5MoyJbjgdLkeWmPb1k9YIDNfc0Hhzl'
        u'itPh81C9NFX4AIhAMMHxu0gPhO8GHZS72mG8Txh98ka3lf9yFbTyyyIoePR',
    'clientData': u'eyJvcmlnaW4iOiAiaHR0cDovL2xvY2FsaG9zdCIsICJjaGFsbGVuZ2UiO'
        u'iAicm8tMXBKakdxRzhJanNhYXZFT043ZW5odUJSTFZzR3BBNnVNSWM2VmxlNCIsICJ0'
        u'eXAiOiAibmF2aWdhdG9yLmlkLmZpbmlzaEVucm9sbG1lbnQifQ',
}


DEVICE_DATA = {
    'version': u'U2F_V2',
    'transports': None,
    'appId': u'http://localhost',
    'publicKey':
        u'BEVUOmClp_Gug39G3sVxFA3wtsEu6Od32JrKn5QqRPW28gmEV59Jv0ZAeQ4V3bKPj0i'
        u'wcDckdZO61b8bAPj03Cs', 'keyHandle': u'j9xy6-W8rMp1WS7EsIfYWNY-cdXHa'
        u'cq23sQS3hqJtPAuKF6nFuTFPMiX5VaZxevCJmW-Q3KNvSAfJdtInsl1JQ',
}

BASE_URL = 'http://localhost'
TEST_VALUE = b'U2F Test Token'

ADDON_PATH = 'odoo.addons.auth_u2f'
CONTROLLER_PATH = ADDON_PATH + '.controllers.main'
DEVICE_PATH = ADDON_PATH + '.models.u2f_device'

_logger = logging.getLogger(__name__)


@mock.patch(CONTROLLER_PATH + '.request')
class TestAuthU2f(TransactionCase):

    @mock.patch(DEVICE_PATH + '.request')
    def setUp(self, request_mock):
        super(TestAuthU2f, self).setUp()

        self.env['ir.config_parameter'].sudo().set_param(
            'web.base.url', BASE_URL)

        self.controller = AuthU2FController()
        self.login = U2FLogin()

        self.test_user = self.env.ref('base.user_root')

        request_mock.session.u2f_last_registration_challenge = REQUEST_DATA

        self.device = self.env['u2f.device'].create({
            'name': 'Test Authenticator',
            'json': json.dumps(RESPONSE_DATA),
            'user_id': self.test_user.id,
            'default': True,
        })

        # Needed when tests are run with no prior requests (e.g. on a new DB)
        patcher = mock.patch('odoo.http.request')
        self.addCleanup(patcher.stop)
        patcher.start()

    def test_login(self, request_mock):
        request_mock.env = self.env
        request_mock.session.uid = self.test_user.id
        request_mock.session.u2f_last_registration_challenge = REQUEST_DATA
        request_mock.render.return_value = b"OK"

        response = self.controller.u2f_login()
        request_mock.render.assert_called_once_with('auth_u2f.login', mock.ANY)
        self.assertEqual(response.get_data(), request_mock.render.return_value)

    def test_login_fail_no_device(self, request_mock):
        self.device.unlink()
        request_mock.env = self.env
        request_mock.session.uid = self.test_user.id

        try:
            self.controller.u2f_login()
        except AccessDenied:
            pass

    @mock.patch(CONTROLLER_PATH + '.http')
    def test_login_post(self, http_mock, request_mock):
        request_mock.env = self.env
        request_mock.session.uid = self.test_user.id
        request_mock.render.side_effect = lambda x: x
        request_mock.httprequest.method = 'POST'

        return_value = TEST_VALUE
        http_mock.redirect_with_hash.return_value = return_value

        response = self.controller.u2f_login(TEST_VALUE, '/u2f/ok')

        http_mock.redirect_with_hash.assert_called_once_with('/u2f/ok')
        self.assertEqual(request_mock.session.u2f_token_response, TEST_VALUE)
        self.assertEqual(response.get_data(), return_value)

    @mock.patch(CONTROLLER_PATH + '.Home.web_client')
    def test_web_client(self, super_mock, request_mock):
        auth_mock = mock.MagicMock()
        request_mock.env = {'ir.http': auth_mock}
        request_mock.session.uid = self.test_user.id

        super_mock.return_value = TEST_VALUE

        response = self.login.web_client()
        self.assertTrue(super_mock.call_count)
        self.assertTrue(auth_mock._authenticate.call_count)
        self.assertEqual(response.get_data(), super_mock.return_value)

    @mock.patch(CONTROLLER_PATH + '.werkzeug.utils.redirect')
    @mock.patch(CONTROLLER_PATH + '.Home.web_client')
    def test_web_client_fail(self, super_mock, redirect_mock, request_mock):
        auth_mock = mock.MagicMock()
        auth_mock.side_effect = U2FAuthenticationError()
        request_mock.env = {'ir.http': mock.MagicMock(_authenticate=auth_mock)}
        redirect_mock.return_value = TEST_VALUE

        response = self.login.web_client()

        self.assertTrue(auth_mock.call_count)
        self.assertTrue(super_mock.call_count)
        redirect_mock.assert_called_once_with('/web/u2f/login', 303)
        self.assertEqual(response.get_data(), TEST_VALUE)
