# Copyright 2016 SYLEAM
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from datetime import timedelta
from unittest import mock
from urllib.parse import parse_qs, urlparse

from odoo import fields
from odoo.http.requestlib import Request
from odoo.tests.common import HttpCase, tagged

_logger = logging.getLogger(__name__)


class TestResponse:
    """Expose a requests response with the werkzeug test response API"""

    def __init__(self, response):
        self.status_code = response.status_code
        self.headers = response.headers
        self.data = response.content


@tagged("post_install", "-at_install")
class OAuthProviderControllerTransactionCase(HttpCase):
    # The tests live in mixins shared by the application types
    allow_inherited_tests_method = True

    def setUp(self, application_type):
        super().setUp()

        # Tests post without CSRF tokens
        self.csrf_patcher = mock.patch.object(
            Request, "validate_csrf", return_value=True
        )
        self.csrf_patcher.start()
        self.addCleanup(self.csrf_patcher.stop)

        # Own user, the tests do not depend on demo data
        self.user_password = "oauth-provider-test"
        self.user = self.env["res.users"].create(
            {
                "name": "OAuth Provider Test User",
                "login": "oauth_provider_test",
                "email": "oauth_provider_test@example.com",
                "city": "Lyon",
                "password": self.user_password,
                "group_ids": [(6, 0, [self.env.ref("base.group_user").id])],
            }
        )
        self.logged_user = False

        # Initialize common stuff
        self.redirect_uri_base = "http://example.com"
        self.filter = self.env["ir.filters"].create(
            {
                "name": "Current user",
                "model_id": "res.users",
                "domain": "[('id', '=', uid)]",
            }
        )
        self.client = self.env["oauth.provider.client"].create(
            {
                "name": "Client",
                "identifier": "client",
                "application_type": application_type,
                "redirect_uri_ids": [(0, 0, {"name": self.redirect_uri_base})],
                "scope_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "Email",
                            "code": "email",
                            "description": "Access to your email address.",
                            "model_id": self.env.ref("base.model_res_users").id,
                            "filter_id": self.filter.id,
                            "field_ids": [
                                (
                                    6,
                                    0,
                                    [self.env.ref("base.field_res_users__email").id],
                                ),
                            ],
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "name": "Profile",
                            "code": "profile",
                            "description": """
                                Access to your profile details (name, etc.)
                            """,
                            "model_id": self.env.ref("base.model_res_users").id,
                            "filter_id": self.filter.id,
                            "field_ids": [
                                (
                                    6,
                                    0,
                                    [
                                        self.env.ref("base.field_res_users__name").id,
                                        self.env.ref("base.field_res_users__city").id,
                                    ],
                                ),
                            ],
                        },
                    ),
                ],
            }
        )

    def login(self, username, password):
        self.authenticate(username, password)
        self.logged_user = self.env["res.users"].search([("login", "=", username)])

    def logout(self):
        res = super().logout()
        self.logged_user = False
        return res

    def get_request(self, uri, data=None, headers=None):
        """Execute a GET request on the test server"""
        headers = dict(headers or {})
        return TestResponse(
            self.url_open(uri, params=data, headers=headers, allow_redirects=False)
        )

    def post_request(self, uri, data=None, headers=None):
        """Execute a POST request on the test server"""
        headers = dict(headers or {})
        return TestResponse(
            self.url_open(
                uri,
                data=data or {},
                headers=headers,
                allow_redirects=False,
                method="POST",
            )
        )

    def new_token(self):
        return self.env["oauth.provider.token"].create(
            {
                "token": "token",
                "token_type": "Bearer",
                "refresh_token": "refresh token",
                "client_id": self.client.id,
                "user_id": self.user.id,
                "expires_at": fields.Datetime.to_string(
                    fields.Datetime.now() + timedelta(seconds=3600)
                ),
            }
        )

    def assertUrlsEqual(self, url1, url2):
        """Test if strings are the same url, ignoring order of parameters"""
        u1 = urlparse(url1)
        u2 = urlparse(url2)
        self.assertEqual(u1[:4], u2[:4])
        self.assertEqual(parse_qs(u1.query), parse_qs(u2.query))
