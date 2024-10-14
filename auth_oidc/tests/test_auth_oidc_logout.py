# Copyright 2021 ACSONE SA/NV <https://acsone.eu>
# License: AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

import contextlib
import logging
from urllib.parse import parse_qsl, urljoin, urlparse

from werkzeug.urls import url_encode

import odoo
from odoo.tests import common
from odoo.tools.misc import DotDict

from odoo.addons.website.tools import MockRequest

from ..controllers.main import OpenIDLogout

BASE_URL = "http://localhost:%s" % odoo.tools.config["http_port"]
CLIENT_ID = "auth_oidc-test"
LOGIN_PATH = "/web/login"
OIDC_BASE_LOGOUT_URL = "http://keycloak"
OIDC_LOGOUT_PATH = "/logout"

logger = logging.getLogger(__name__)


@contextlib.contextmanager
def create_request(env, user_id, user_logout_func):
    with MockRequest(env) as request:
        request.httprequest.url_root = BASE_URL + "/"
        request.session = DotDict(uid=user_id, logout=user_logout_func)
        yield request


class TestOpenIDLogout(common.HttpCase):
    @staticmethod
    def mock_logout_user(keep_db):
        logger.info("Logging out user in Odoo")

    def setUp(self):
        super().setUp()
        # search our test provider and bind the demo user to it
        self.provider = self.env["auth.oauth.provider"].search(
            [("client_id", "=", CLIENT_ID)]
        )
        self.assertEqual(len(self.provider), 1)

    def _prepare_login_test_user(self, provider_id):
        user = self.env.ref("base.user_demo")
        user.write({"oauth_provider_id": provider_id, "oauth_uid": user.login})
        return user

    def _set_test_oidc_logout_url(self, end_session_endpoint):
        self.provider.write({"end_session_endpoint": end_session_endpoint})

    def test_skip_oidc_logout_for_user(self):
        """Test that oidc logout is skipped if user is not associated to a provider"""
        user = self._prepare_login_test_user(None)
        with create_request(self.env, user.id, self.mock_logout_user):
            resp = OpenIDLogout().logout()
            self.assertEqual(LOGIN_PATH, resp.location)

    def test_skip_oidc_logout_for_all_users(self):
        """Test that oidc logout is skipped for all users if provider has no logout url"""
        self.assertFalse(self.provider.end_session_endpoint)
        user = self._prepare_login_test_user(self.provider)
        with create_request(self.env, user.id, self.mock_logout_user):
            resp = OpenIDLogout().logout()
            self.assertEqual(LOGIN_PATH, resp.location)

    def test_oidc_logout(self):
        """Test that oidc logout"""
        self._set_test_oidc_logout_url(urljoin(OIDC_BASE_LOGOUT_URL, OIDC_LOGOUT_PATH))
        user = self._prepare_login_test_user(self.provider)
        with create_request(self.env, user.id, self.mock_logout_user):
            resp = OpenIDLogout().logout()
            self.assertTrue(resp.location.startswith(OIDC_BASE_LOGOUT_URL))
            actual_components = urlparse(resp.location)
            self.assertEqual(OIDC_LOGOUT_PATH, actual_components.path)
            actual_params = dict(parse_qsl(actual_components.query))
            self.assertEqual(CLIENT_ID, actual_params["client_id"])
            self.assertEqual(
                urljoin(BASE_URL, LOGIN_PATH), actual_params["post_logout_redirect_uri"]
            )

    def test_oidc_logout_with_params(self):
        """Test that params both in the logout and redirect urls are preserved"""
        logout_url_params = {"param_1": 1, "param_2": 2}
        oidc_logout_path = "{}?{}".format(
            OIDC_LOGOUT_PATH, url_encode(logout_url_params)
        )
        logout_url = urljoin(OIDC_BASE_LOGOUT_URL, oidc_logout_path)
        self._set_test_oidc_logout_url(logout_url)
        user = self._prepare_login_test_user(self.provider)
        with create_request(self.env, user.id, self.mock_logout_user):
            redirect_path = "{}?{}".format(
                LOGIN_PATH, url_encode({"param_3": 3, "param_4": 4})
            )
            params = {}
            params.update(logout_url_params)
            params["client_id"] = CLIENT_ID
            params["post_logout_redirect_uri"] = urljoin(BASE_URL, redirect_path)
            resp = OpenIDLogout().logout(redirect_path)
            self.assertTrue(resp.location.startswith(OIDC_BASE_LOGOUT_URL))
            actual_components = urlparse(resp.location)
            self.assertEqual(OIDC_LOGOUT_PATH, actual_components.path)
            actual_params = dict(parse_qsl(actual_components.query))
            self.assertEqual(CLIENT_ID, actual_params["client_id"])
            self.assertEqual("1", actual_params["param_1"])
            self.assertEqual("2", actual_params["param_2"])
            post_logout_url = actual_params["post_logout_redirect_uri"]
            self.assertTrue(post_logout_url.startswith(BASE_URL))
            post_logout_components = urlparse(post_logout_url)
            self.assertEqual(LOGIN_PATH, post_logout_components.path)
            post_logout_params = dict(parse_qsl(post_logout_components.query))
            self.assertEqual("3", post_logout_params["param_3"])
            self.assertEqual("4", post_logout_params["param_4"])

    def test_oidc_logout_with_absolute_redirect_url(self):
        """Test that oidc logout allows an absolute redirect url"""
        self._set_test_oidc_logout_url(urljoin(OIDC_BASE_LOGOUT_URL, OIDC_LOGOUT_PATH))
        user = self._prepare_login_test_user(self.provider)
        with create_request(self.env, user.id, self.mock_logout_user):
            resp = OpenIDLogout().logout(BASE_URL)
            self.assertTrue(resp.location.startswith(OIDC_BASE_LOGOUT_URL))
            actual_components = urlparse(resp.location)
            self.assertEqual(OIDC_LOGOUT_PATH, actual_components.path)
            actual_params = dict(parse_qsl(actual_components.query))
            self.assertEqual(CLIENT_ID, actual_params["client_id"])
            self.assertEqual(BASE_URL, actual_params["post_logout_redirect_uri"])

    def test_oidc_logout_skip_confirmation(self):
        """Test that oidc logout skips confirmation"""
        id_token = "test-id-token"
        self._set_test_oidc_logout_url(urljoin(OIDC_BASE_LOGOUT_URL, OIDC_LOGOUT_PATH))
        self.provider.write({"skip_logout_confirmation": True})
        user = self._prepare_login_test_user(self.provider)
        user.write({"oauth_id_token": id_token})
        with create_request(self.env, user.id, self.mock_logout_user):
            resp = OpenIDLogout().logout()
            self.assertTrue(resp.location.startswith(OIDC_BASE_LOGOUT_URL))
            actual_components = urlparse(resp.location)
            self.assertEqual(OIDC_LOGOUT_PATH, actual_components.path)
            actual_params = dict(parse_qsl(actual_components.query))
            self.assertEqual(CLIENT_ID, actual_params["client_id"])
            self.assertEqual(id_token, actual_params["id_token_hint"])
            self.assertEqual(
                urljoin(BASE_URL, LOGIN_PATH), actual_params["post_logout_redirect_uri"]
            )

    def test_oidc_logout_not_skip_confirmation_if_no_id_token(self):
        """Test that oidc logout does not skip confirmation if user has no oauth_id_token"""
        self._set_test_oidc_logout_url(urljoin(OIDC_BASE_LOGOUT_URL, OIDC_LOGOUT_PATH))
        self.provider.write({"skip_logout_confirmation": True})
        user = self._prepare_login_test_user(self.provider)
        with create_request(self.env, user.id, self.mock_logout_user):
            resp = OpenIDLogout().logout()
            self.assertTrue(resp.location.startswith(OIDC_BASE_LOGOUT_URL))
            actual_components = urlparse(resp.location)
            self.assertEqual(OIDC_LOGOUT_PATH, actual_components.path)
            actual_params = dict(parse_qsl(actual_components.query))
            self.assertEqual(CLIENT_ID, actual_params["client_id"])
            self.assertIsNone(actual_params.get("id_token_hint"))
            self.assertEqual(
                urljoin(BASE_URL, LOGIN_PATH), actual_params["post_logout_redirect_uri"]
            )

    def test_oidc_logout_not_skip_confirmation_if_not_enabled(self):
        """Test that oidc logout skips confirmation"""
        id_token = "test-id-token"
        self._set_test_oidc_logout_url(urljoin(OIDC_BASE_LOGOUT_URL, OIDC_LOGOUT_PATH))
        self.provider.write({"skip_logout_confirmation": False})
        user = self._prepare_login_test_user(self.provider)
        user.write({"oauth_id_token": id_token})
        with create_request(self.env, user.id, self.mock_logout_user):
            resp = OpenIDLogout().logout()
            self.assertTrue(resp.location.startswith(OIDC_BASE_LOGOUT_URL))
            actual_components = urlparse(resp.location)
            self.assertEqual(OIDC_LOGOUT_PATH, actual_components.path)
            actual_params = dict(parse_qsl(actual_components.query))
            self.assertEqual(CLIENT_ID, actual_params["client_id"])
            self.assertIsNone(actual_params.get("id_token_hint"))
            self.assertEqual(
                urljoin(BASE_URL, LOGIN_PATH), actual_params["post_logout_redirect_uri"]
            )
