# Copyright 2016 SYLEAM
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from datetime import datetime, timedelta
from urllib.parse import parse_qs, urlparse

import mock
from werkzeug.test import Client
from werkzeug.wrappers import BaseResponse

from odoo import fields
from odoo.service import wsgi_server
from odoo.tests.common import TransactionCase
from odoo.tools.misc import consteq

_logger = logging.getLogger(__name__)


class OAuthProviderControllerTransactionCase(TransactionCase):
    def setUp(self, application_type):
        super().setUp()

        # Initialize controller test stuff
        self.werkzeug_environ = {
            "REMOTE_ADDR": "127.0.0.1",
        }
        self.user = self.env.ref("base.user_demo")
        self.logged_user = False
        self.initialize_test_client()

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
                            "description": "Access to your profile details (name, etc.)",
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

    def initialize_test_client(self):
        # Instantiate a test client
        self.test_client = Client(wsgi_server.application, BaseResponse)
        # Select the database
        self.get_request("/web", data={"db": self.env.cr.dbname})

    def login(self, username, password):
        # Login as demo user
        self.post_request(
            "/web/login",
            data={
                "login": username,
                "password": password,
            },
        )
        self.logged_user = self.env["res.users"].search([("login", "=", username)])

    def logout(self):
        # Login as demo user
        self.get_request("/web/session/logout")
        self.logged_user = False

    @mock.patch("odoo.http.WebRequest.env", new_callable=mock.PropertyMock)
    def get_request(self, uri, request_env, data=None, headers=None):
        """Execute a GET request on the test client"""
        # Mock the http request's environ to allow it to see test records
        user = self.logged_user or self.env.ref("base.public_user")
        request_env.return_value = self.env(user=user)

        return self.test_client.get(
            uri, query_string=data, environ_base=self.werkzeug_environ, headers=headers
        )

    @mock.patch("odoo.http.WebRequest.env", new_callable=mock.PropertyMock)
    @mock.patch("odoo.http.WebRequest.validate_csrf")
    def post_request(self, uri, validate_csrf, request_env, data=None, headers=None):
        """Execute a POST request on the test client"""
        # Mock the http request's environ to allow it to see test records
        user = self.logged_user or self.env.ref("base.public_user")
        request_env.return_value = self.env(user=user)
        # Disable CSRF tokens check during tests
        validate_csrf.return_value = consteq("", "")

        return self.test_client.post(
            uri, data=data, environ_base=self.werkzeug_environ, headers=headers
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
                    datetime.now() + timedelta(seconds=3600)
                ),
            }
        )

    def assertUrlsEqual(self, url1, url2):
        """Test if strings are the same url, ignoring order of parameters"""
        u1 = urlparse(url1)
        u2 = urlparse(url2)
        self.assertEqual(u1[:4], u2[:4])
        self.assertEqual(parse_qs(u1.query), parse_qs(u2.query))
