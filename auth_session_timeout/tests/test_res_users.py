# Copyright 2016-2017 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import time
from contextlib import contextmanager

import mock

from odoo.http import SessionExpiredException
from odoo.tests.common import TransactionCase


class TestResUsers(TransactionCase):
    def setUp(self):
        super(TestResUsers, self).setUp()
        self.ResUsers = self.env["res.users"]

    @contextmanager
    def _mock_assets(self, assets=None):
        """It provides mocked imports from res_users.py
        :param assets: (list) Name of imports to mock. Mocks `http` if None
        :return: (dict) Dictionary of mocks, keyed by module name
        """
        if assets is None:
            assets = ["http"]
        patches = {name: mock.DEFAULT for name in assets}
        with mock.patch.multiple(
            "odoo.addons.auth_session_timeout.models.res_users", **patches
        ) as mocks:
            yield mocks

    def _auth_timeout_check(self, http_mock):
        """It wraps ``_auth_timeout_check`` for easier calling"""
        self.db = mock.MagicMock()
        self.uid = mock.MagicMock()
        self.passwd = mock.MagicMock()
        return self.ResUsers._auth_timeout_check()

    def test_session_validity_no_request(self):
        """It should return immediately if no request"""
        with self._mock_assets() as assets:
            assets["http"].request = False
            res = self._auth_timeout_check(assets["http"])
            self.assertFalse(res)

    def test_session_validity_gets_session(self):
        """It should call get the session file for the session id"""
        with self._mock_assets() as assets:
            session = assets["http"].request.session.get
            session.return_value = time.time()
            self._auth_timeout_check(assets["http"])

    def test_session_validity_logout(self):
        """It should log out of session if past deadline"""
        with self._mock_assets(["http"]) as assets:
            session = assets["http"].request.session.get
            session.return_value = time.time() - 10000
            with self.assertRaises(SessionExpiredException):
                self._auth_timeout_check(assets["http"])
            assets["http"].request.session.logout.assert_called_once_with(
                keep_db=True,
            )
