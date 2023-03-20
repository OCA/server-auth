# Copyright 2016 LasLabs Inc.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from contextlib import contextmanager
from datetime import datetime, timedelta
from unittest import mock

from werkzeug.urls import url_parse

from odoo.exceptions import UserError
from odoo.http import Response, _request_stack
from odoo.tests.common import HttpCase, TransactionCase

from ..controllers import main

IMPORT = "odoo.addons.password_security.controllers.main"


class EndTestException(Exception):
    """It allows for isolation of resources by raise"""


class MockResponse(object):
    def __new__(cls):
        return mock.Mock(spec=Response)


class MockPassError(UserError):
    def __init__(self):
        super(MockPassError, self).__init__("Message")


class TestPasswordSecurityHome(TransactionCase):
    def setUp(self):
        super(TestPasswordSecurityHome, self).setUp()
        self.main_comp = self.env.ref("base.main_company")
        self.main_comp.password_policy_enabled = True
        self.PasswordSecurityHome = main.PasswordSecurityHome
        self.password_security_home = self.PasswordSecurityHome()
        self.passwd = "I am a password!"
        self.qcontext = {
            "password": self.passwd,
        }
        _request_stack.push(
            mock.Mock(
                env=self.env,
            )
        )
        self.addCleanup(_request_stack.pop)

    @contextmanager
    def mock_assets(self):
        """It mocks and returns assets used by this controller"""
        methods = [
            "do_signup",
            "web_login",
            "web_auth_signup",
            "web_auth_reset_password",
        ]
        with mock.patch.multiple(
            main.AuthSignupHome, **{m: mock.DEFAULT for m in methods}
        ) as _super:
            mocks = {}
            for method in methods:
                mocks[method] = _super[method]
                mocks[method].return_value = MockResponse()
            with mock.patch("%s.request" % IMPORT) as request:
                with mock.patch("%s.ensure_db" % IMPORT) as ensure:
                    with mock.patch("%s.http" % IMPORT) as http:
                        http.request.redirect.return_value = MockResponse()
                        mocks.update(
                            {
                                "request": request,
                                "ensure_db": ensure,
                                "http": http,
                            }
                        )
                        yield mocks

    def test_do_signup_check(self):
        """It should check password on user"""
        with self.mock_assets() as assets:
            check_password = assets["request"].env.user._check_password
            check_password.side_effect = EndTestException
            with self.assertRaises(EndTestException):
                self.password_security_home.do_signup(self.qcontext)
            check_password.assert_called_once_with(
                self.passwd,
            )

    def test_do_signup_return(self):
        """It should return result of super"""
        with self.mock_assets() as assets:
            res = self.password_security_home.do_signup(self.qcontext)
            self.assertEqual(assets["do_signup"](), res)

    def test_web_login_ensure_db(self):
        """It should verify available db"""
        with self.mock_assets() as assets:
            assets["ensure_db"].side_effect = EndTestException
            with self.assertRaises(EndTestException):
                self.password_security_home.web_login()

    def test_web_login_super(self):
        """It should call superclass w/ proper args"""
        expect_list = [1, 2, 3]
        expect_dict = {"test1": "good1", "test2": "good2"}
        with self.mock_assets() as assets:
            assets["web_login"].side_effect = EndTestException
            with self.assertRaises(EndTestException):
                self.password_security_home.web_login(*expect_list, **expect_dict)
            assets["web_login"].assert_called_once_with(*expect_list, **expect_dict)

    def test_web_login_log_out_if_expired(self):
        """It should log out user if password expired"""
        with self.mock_assets() as assets:
            request = assets["request"]
            request.httprequest.method = "POST"
            user = request.env["res.users"].sudo().browse()
            user._password_has_expired.return_value = True
            self.password_security_home.web_login()

            logout_mock = request.session.logout
            logout_mock.assert_called_once_with(keep_db=True)

    def test_web_login_redirect(self):
        """It should redirect w/ hash to reset after expiration"""
        with self.mock_assets() as assets:
            request = assets["request"]
            request.httprequest.method = "POST"
            user = request.env["res.users"].sudo().browse()
            user._password_has_expired.return_value = True
            res = self.password_security_home.web_login()
            self.assertEqual(
                request.redirect(),
                res,
            )

    def test_web_auth_signup_valid(self):
        """It should return super if no errors"""
        with self.mock_assets() as assets:
            res = self.password_security_home.web_auth_signup()
            self.assertEqual(
                assets["web_auth_signup"](),
                res,
            )

    def test_web_auth_signup_invalid_qcontext(self):
        """It should catch PassError and get signup qcontext"""
        with self.mock_assets() as assets:
            with mock.patch.object(
                main.AuthSignupHome,
                "get_auth_signup_qcontext",
            ) as qcontext:
                assets["web_auth_signup"].side_effect = MockPassError
                qcontext.side_effect = EndTestException
                with self.assertRaises(EndTestException):
                    self.password_security_home.web_auth_signup()

    def test_web_auth_signup_invalid_render(self):
        """It should render & return signup form on invalid"""
        with self.mock_assets() as assets:
            with mock.patch.object(
                main.AuthSignupHome, "get_auth_signup_qcontext", spec=dict
            ) as qcontext:
                assets["web_auth_signup"].side_effect = MockPassError
                res = self.password_security_home.web_auth_signup()
                assets["request"].render.assert_called_once_with(
                    "auth_signup.signup",
                    qcontext(),
                )
                self.assertEqual(
                    assets["request"].render(),
                    res,
                )


@mock.patch("odoo.http.WebRequest.validate_csrf", return_value=True)
class LoginCase(HttpCase):
    def setUp(self):
        super(LoginCase, self).setUp()
        self.main_comp = self.env.ref("base.main_company")
        self.main_comp.password_policy_enabled = True

    def test_web_login_authenticate(self, *args):
        """It should allow authenticating by login"""
        response = self.url_open(
            "/web/login",
            {"login": "admin", "password": "admin"},
        )
        # Redirected to /web because it succeeded
        path = url_parse(response.url).path
        self.assertEqual(path, "/web")
        self.assertEqual(response.status_code, 200)

    def test_web_login_authenticate_fail(self, *args):
        """It should fail auth"""
        response = self.url_open(
            "/web/login",
            {"login": "admin", "password": "noadmin"},
        )
        self.assertIn(
            "Wrong login/password",
            response.text,
        )

    def test_web_login_expire_pass(self, *args):
        """It should expire password if necessary"""
        three_days_ago = datetime.now() - timedelta(days=3)
        with self.cursor() as cr:
            env = self.env(cr)
            user = env["res.users"].search([("login", "=", "admin")])
            user.password_write_date = three_days_ago
            user.company_id.password_expiration = 1
        response = self.url_open(
            "/web/login",
            {"login": "admin", "password": "admin"},
        )
        path = url_parse(response.url).path
        self.assertEqual(path, "/web/reset_password")
