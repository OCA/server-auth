# Copyright 2021 ACSONE SA/NV <https://acsone.eu>
# License: AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from unittest.mock import Mock, patch

from odoo.http import Response
from odoo.tests import common

from odoo.addons.website.tools import MockRequest

from ..controllers.main import OAuthAutoLogin

LOGIN_URL = "http://localhost/web/login"


class TestOauthAutoLogin(common.HttpCase):
    def mock_redirect(self, redirect_url, code, local):
        """Mock redirect to capture parameters"""
        self.redirect_url = redirect_url
        self.redirect_code = code
        self.is_local_redirect = local
        return Mock()

    @patch("odoo.addons.auth_oauth.controllers.main.OAuthLogin.web_login")
    def test_skip_auto_login_if_already_logged_in(self, mock_web_login):
        """Test that auto login is skipped if user is logged in"""
        mock_session = Mock()
        response = Response()
        mock_web_login.return_value = response
        with MockRequest(self.env) as request:
            request.session = mock_session
            result = OAuthAutoLogin().web_login.__wrapped__(OAuthAutoLogin())
            self.assertEqual(response, result)

    @patch("odoo.addons.auth_oauth.controllers.main.OAuthLogin.web_login")
    def test_skip_auto_login_if_no_autologin_parameter_exists(self, mock_web_login):
        """Test that auto login is skipped if no_autologin parameter exists"""
        mock_session = Mock()
        response = Response()
        mock_web_login.return_value = response
        with MockRequest(self.env) as request:
            request.session = mock_session
            mock_session.uid = False
            request.httprequest.url = LOGIN_URL + "?no_autologin"
            result = OAuthAutoLogin().web_login.__wrapped__(OAuthAutoLogin())
            self.assertEqual(response, result)

    @patch("odoo.addons.auth_oauth.controllers.main.OAuthLogin.web_login")
    def test_skip_auto_login_if_oauth_error_parameter_exists(self, mock_web_login):
        """Test that auto login is skipped if oauth_error parameter exists"""
        mock_session = Mock()
        response = Response()
        mock_web_login.return_value = response
        with MockRequest(self.env) as request:
            request.session = mock_session
            mock_session.uid = False
            request.httprequest.url = LOGIN_URL + "?oauth_error=1"
            result = OAuthAutoLogin().web_login.__wrapped__(OAuthAutoLogin())
            self.assertEqual(response, result)

    @patch("odoo.addons.auth_oauth.controllers.main.OAuthLogin.web_login")
    def test_skip_auto_login_if_error_parameter_exists(self, mock_web_login):
        """Test that auto login is skipped if error parameter exists"""
        mock_session = Mock()
        response = Response()
        mock_web_login.return_value = response
        with MockRequest(self.env) as request:
            request.session = mock_session
            mock_session.uid = False
            request.httprequest.url = LOGIN_URL + "?error=test"
            result = OAuthAutoLogin().web_login.__wrapped__(OAuthAutoLogin())
            self.assertEqual(response, result)

    @patch("odoo.addons.auth_oauth.controllers.main.OAuthLogin.web_login")
    def test_skip_auto_login_if_no_provider_has_autologin_set(self, mock_web_login):
        """Test that auto login is skipped if error parameter exists"""
        instance = OAuthAutoLogin()
        mock_session = Mock()
        response = Response()
        mock_web_login.return_value = response
        provider = {}
        provider["autologin"] = False
        provider["auth_link"] = "https://keycloak.test"
        providers = [provider]
        with (
            MockRequest(self.env) as request,
            patch.object(instance, "list_providers", return_value=providers),
        ):
            request.session = mock_session
            mock_session.uid = False
            request.httprequest.url = LOGIN_URL
            result = instance.web_login.__wrapped__(instance)
            self.assertEqual(response, result)

    @patch("odoo.addons.auth_oauth.controllers.main.OAuthLogin.web_login")
    def test_skip_auto_login_if_the_provider_has_no_auth_link(self, mock_web_login):
        """Test that auto login is skipped if error parameter exists"""
        instance = OAuthAutoLogin()
        mock_session = Mock()
        response = Response()
        mock_web_login.return_value = response
        provider = {}
        provider["autologin"] = True
        providers = [provider]
        with (
            MockRequest(self.env) as request,
            patch.object(instance, "list_providers", return_value=providers),
        ):
            request.session = mock_session
            mock_session.uid = False
            request.httprequest.url = LOGIN_URL
            result = instance.web_login.__wrapped__(instance)
            self.assertEqual(response, result)

    @patch("odoo.addons.auth_oauth.controllers.main.OAuthLogin.web_login")
    def test_oauth_auto_login_with_enabled_provider(self, mock_web_login):
        """Test that auto login works if enabled"""
        instance = OAuthAutoLogin()
        mock_session = Mock()
        response = Response()
        mock_web_login.return_value = response
        provider_1 = {}
        provider_1["autologin"] = False
        provider_1["auth_link"] = "https://keycloak1.test"
        auth_link_2 = "https://keycloak2.test"
        provider_2 = {}
        provider_2["autologin"] = True
        provider_2["auth_link"] = auth_link_2
        providers = [provider_1, provider_2]
        with (
            MockRequest(self.env) as request,
            patch.object(instance, "list_providers", return_value=providers),
        ):
            request.session = mock_session
            mock_session.uid = False
            request.httprequest.url = LOGIN_URL
            request.httprequest.method = "GET"
            request.redirect = self.mock_redirect

            instance.web_login.__wrapped__(instance)

            # Verify redirect was called correctly
            self.assertEqual(auth_link_2, self.redirect_url)
            self.assertEqual(303, self.redirect_code)
            self.assertFalse(self.is_local_redirect)

            # Verify super was NOT called
            self.assertFalse(mock_web_login.called)
