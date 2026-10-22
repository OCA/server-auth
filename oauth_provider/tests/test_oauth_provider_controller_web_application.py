# Copyright 2016 SYLEAM
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import json
import logging

from odoo import fields

from .common_test_controller import OAuthProviderControllerTransactionCase
from .common_test_oauth_provider_controller import (
    TestOAuthProviderAurhorizeController,
    TestOAuthProviderOtherinfoController,
    TestOAuthProviderRefreshTokenController,
    TestOAuthProviderRevokeTokenController,
    TestOAuthProviderTokeninfoController,
    TestOAuthProviderUserinfoController,
)

_logger = logging.getLogger(__name__)

try:
    import oauthlib
except ImportError:
    _logger.debug("Cannot `import oauthlib`.")


class TestOAuthProviderController(
    OAuthProviderControllerTransactionCase,
    TestOAuthProviderRefreshTokenController,
    TestOAuthProviderAurhorizeController,
    TestOAuthProviderTokeninfoController,
    TestOAuthProviderUserinfoController,
    TestOAuthProviderOtherinfoController,
    TestOAuthProviderRevokeTokenController,
):
    def setUp(self):
        super().setUp("web application")

    def new_code(self):
        # Configure the client to skip the authorization page
        self.client.skip_authorization = True

        # Call the authorize method with good values
        state = "Some custom state"
        self.login(self.user.login, self.user_password)
        response = self.get_request(
            "/oauth2/authorize",
            data={
                "client_id": self.client.identifier,
                "response_type": self.client.response_type,
                "redirect_uri": self.redirect_uri_base,
                "scope": self.client.scope_ids[0].code,
                "state": state,
            },
        )
        # A new authorization code should have been generated
        # We can safely pick the latest generated code here, because no other
        # code could have been generated during the test
        code = self.env["oauth.provider.authorization.code"].search(
            [
                ("client_id", "=", self.client.id),
            ],
            order="id DESC",
            limit=1,
        )
        # The response should be a redirect to the redirect URI, with the
        # authorization_code added as GET parameter
        self.assertEqual(response.status_code, 302)
        query_string = oauthlib.common.urlencode(
            {"state": state, "code": code.code}.items()
        )
        self.assertUrlsEqual(
            response.headers["Location"],
            f"{self.redirect_uri_base}?{query_string}",
        )
        self.assertEqual(code.user_id, self.user)

        self.logout()

        return code

    def test_token_error_missing_session(self):
        """Check /oauth2/token without any session set

        Must return an invalid_client_id error
        """
        response = self.post_request("/oauth2/token")
        response_text = response.data.decode("utf8")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(json.loads(response_text), {"error": "invalid_client_id"})

    def test_token_error_missing_arguments(self):
        """Check /oauth2/token without any argument

        Must return an invalid_client_id error
        """
        # Generate an authorization code to set the session
        self.new_code()

        response = self.post_request("/oauth2/token")
        response_text = response.data.decode("utf8")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(json.loads(response_text), {"error": "invalid_client_id"})

    def test_token_error_wrong_grant_type(self):
        """Check /oauth2/token with an invalid grant type

        Must return an invalid_client_id error
        """
        # Generate an authorization code to set the session
        self.new_code()

        response = self.post_request(
            "/oauth2/token",
            data={
                "grant_type": "Wrong grant type",
            },
        )
        response_text = response.data.decode("utf8")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(json.loads(response_text), {"error": "invalid_client_id"})

    def test_token_error_missing_code(self):
        """Check /oauth2/token without code

        Must return an invalid_client_id error
        """
        # Generate an authorization code to set the session
        self.new_code()

        response = self.post_request(
            "/oauth2/token",
            data={
                "grant_type": self.client.grant_type,
            },
        )
        response_text = response.data.decode("utf8")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(json.loads(response_text), {"error": "invalid_client_id"})

    def test_token_error_missing_client_id(self):
        """Check /oauth2/token without client

        Must return an invalid_client_id error
        """
        # Generate an authorization code to set the session
        self.new_code()

        response = self.post_request(
            "/oauth2/token",
            data={
                "grant_type": self.client.grant_type,
                "code": "Wrong code",
            },
        )
        response_text = response.data.decode("utf8")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(json.loads(response_text), {"error": "invalid_client_id"})

    def test_token_error_wrong_client_identifier(self):
        """Check /oauth2/token with a wrong client identifier

        Must return an invalid_client_id error
        """
        # Generate an authorization code to set the session
        self.new_code()

        response = self.post_request(
            "/oauth2/token",
            data={
                "grant_type": self.client.grant_type,
                "client_id": "Wrong client identifier",
                "code": "Wrong code",
            },
        )
        response_text = response.data.decode("utf8")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(json.loads(response_text), {"error": "invalid_client_id"})

    def test_token_error_wrong_code(self):
        """Check /oauth2/token with a wrong code

        Must return an invalid_grant error
        """
        # Generate an authorization code to set the session
        self.new_code()

        response = self.post_request(
            "/oauth2/token",
            data={
                "grant_type": self.client.grant_type,
                "client_id": self.client.identifier,
                "code": "Wrong code",
            },
        )
        response_text = response.data.decode("utf8")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(json.loads(response_text), {"error": "invalid_grant"})

    # TODO: this needs more work, as it's correct to pass no redirect_uri
    # to the token endpoint if we didn't pass one to authorize
    def _test_token_error_missing_redirect_uri(self):
        """Check /oauth2/token without redirect_uri

        Must return an access_denied error
        """
        # Generate an authorization code
        code = self.new_code()

        response = self.post_request(
            "/oauth2/token",
            data={
                "grant_type": self.client.grant_type,
                "client_id": self.client.identifier,
                "code": code.code,
            },
        )
        response_text = response.data.decode("utf8")
        # Two possible returned errors, depending on the oauthlib version
        self.assertIn(response.status_code, (400, 401))
        if response.status_code == 400:
            self.assertEqual(
                json.loads(response_text),
                {
                    "error": "invalid_request",
                    "error_description": "Mismatching redirect URI.",
                },
            )
        else:
            self.assertEqual(json.loads(response_text), {"error": "access_denied"})

    def test_token_error_wrong_redirect_uri(self):
        """Check /oauth2/token with a wrong redirect_uri

        Must return an access_denied error
        """
        # Generate an authorization code
        code = self.new_code()

        response = self.post_request(
            "/oauth2/token",
            data={
                "grant_type": self.client.grant_type,
                "client_id": self.client.identifier,
                "code": code.code,
                "redirect_uri": "Wrong redirect URI",
            },
        )
        response_text = response.data.decode("utf8")
        # Two possible returned errors, depending on the oauthlib version
        self.assertIn(response.status_code, (400, 401))
        if response.status_code == 400:
            self.assertEqual(
                json.loads(response_text),
                {
                    "error": "invalid_request",
                    "error_description": "Mismatching redirect URI.",
                },
            )
        else:
            self.assertEqual(json.loads(response_text), {"error": "access_denied"})

    def test_token_error_wrong_client_id(self):
        """Check /oauth2/token with a wrong client id

        Must return an invalid_client_id error
        """
        # Generate an authorization code
        code = self.new_code()

        response = self.post_request(
            "/oauth2/token",
            data={
                "grant_type": self.client.grant_type,
                "client_id": "Wrong client id",
                "code": code.code,
                "redirect_uri": self.redirect_uri_base,
                "scope": self.client.scope_ids[0].code,
            },
        )
        response_text = response.data.decode("utf8")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(json.loads(response_text), {"error": "invalid_client_id"})

    def test_token_error_missing_refresh_token(self):
        """Check /oauth2/token in refresh token mode without refresh token

        Must return an invalid_request error
        """
        # Generate an authorization code to set the session
        self.new_code()

        response = self.post_request(
            "/oauth2/token",
            data={
                "grant_type": "refresh_token",
                "client_id": self.client.identifier,
                "redirect_uri": self.redirect_uri_base,
                "scope": self.client.scope_ids[0].code,
            },
        )
        response_text = response.data.decode("utf8")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            json.loads(response_text),
            {
                "error": "invalid_request",
                "error_description": "Missing refresh token parameter.",
            },
        )

    def test_token_error_invalid_refresh_token(self):
        """Check /oauth2/token in refresh token mode with an invalid refresh token

        Must return an invalid_grant error
        """
        # Generate an authorization code to set the session
        self.new_code()

        response = self.post_request(
            "/oauth2/token",
            data={
                "grant_type": "refresh_token",
                "client_id": self.client.identifier,
                "redirect_uri": self.redirect_uri_base,
                "scope": self.client.scope_ids[0].code,
                "refresh_token": "Wrong refresh token",
            },
        )
        response_text = response.data.decode("utf8")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(json.loads(response_text), {"error": "invalid_grant"})

    def test_authorize_skip_authorization(self):
        """Call /oauth2/authorize while skipping the authorization page"""
        # Configure the client to skip the authorization page
        self.client.skip_authorization = True

        # Call the authorize method with good values
        state = "Some custom state"
        self.login(self.user.login, self.user_password)
        response = self.get_request(
            "/oauth2/authorize",
            data={
                "client_id": self.client.identifier,
                "response_type": self.client.response_type,
                "redirect_uri": self.redirect_uri_base,
                "scope": self.client.scope_ids[0].code,
                "state": state,
            },
        )
        # A new authorization code should have been generated
        # We can safely pick the latest generated code here, because no other
        # code could have been generated during the test
        code = self.env["oauth.provider.authorization.code"].search(
            [
                ("client_id", "=", self.client.id),
            ],
            order="id DESC",
            limit=1,
        )
        # The response should be a redirect to the redirect URI, with the
        # authorization_code added as GET parameter
        self.assertEqual(response.status_code, 302)
        query_string = oauthlib.common.urlencode(
            {
                "state": state,
                "code": code.code,
            }.items()
        )
        self.assertUrlsEqual(
            response.headers["Location"],
            f"{self.redirect_uri_base}?{query_string}",
        )
        self.assertEqual(code.user_id, self.user)

    def test_successful_token_retrieval(self):
        """Check the full process for a WebApplication

        GET, then POST, token and informations retrieval
        """
        # Call the authorize method with good values to fill the session scopes
        # and credentials variables
        state = "Some custom state"
        self.login(self.user.login, self.user_password)
        response = self.get_request(
            "/oauth2/authorize",
            data={
                "client_id": self.client.identifier,
                "response_type": self.client.response_type,
                "redirect_uri": self.redirect_uri_base,
                "scope": self.client.scope_ids[0].code,
                "state": state,
            },
        )
        self.assertEqual(response.status_code, 200)
        response_text = response.data.decode("utf8")
        self.assertTrue(self.client.name in response_text)
        self.assertTrue(self.client.scope_ids[0].name in response_text)
        self.assertTrue(self.client.scope_ids[0].description in response_text)

        # Then, call the POST route to validate the authorization
        response = self.post_request("/oauth2/authorize")
        # A new authorization code should have been generated
        # We can safely pick the latest generated code here, because no other
        # code could have been generated during the test
        code = self.env["oauth.provider.authorization.code"].search(
            [
                ("client_id", "=", self.client.id),
            ],
            order="id DESC",
            limit=1,
        )
        # The response should be a redirect to the redirect URI, with the
        # authorization_code added as GET parameter
        self.assertEqual(response.status_code, 302)
        query_string = oauthlib.common.urlencode(
            {
                "state": state,
                "code": code.code,
            }.items()
        )
        self.assertUrlsEqual(
            response.headers["Location"],
            f"{self.redirect_uri_base}?{query_string}",
        )
        self.assertEqual(code.user_id, self.user)

        self.logout()

        # Now that the user vaidated the authorization, we can ask for a token,
        # using the returned code
        response = self.post_request(
            "/oauth2/token",
            data={
                "client_id": self.client.identifier,
                "redirect_uri": self.redirect_uri_base,
                "scope": self.client.scope_ids[0].code,
                "code": code.code,
                "grant_type": self.client.grant_type,
            },
        )
        response_text = response.data.decode("utf8")
        response_data = json.loads(response_text)
        # A new token should have been generated
        # We can safely pick the latest generated token here, because no other
        # token could have been generated during the test
        token = self.env["oauth.provider.token"].search(
            [
                ("client_id", "=", self.client.id),
            ],
            order="id DESC",
            limit=1,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(token.token, response_data["access_token"])
        self.assertEqual(token.token_type, response_data["token_type"])
        self.assertEqual(token.refresh_token, response_data["refresh_token"])
        self.assertEqual(token.scope_ids, code.scope_ids)
        self.assertEqual(token.user_id, self.user)
        self.assertNotIn("odoo_user_id", response_data)

    def _request_token_with_code(self, code, scope=None):
        data = {
            "client_id": self.client.identifier,
            "redirect_uri": self.redirect_uri_base,
            "code": code.code,
            "grant_type": self.client.grant_type,
        }
        if scope is not None:
            data["scope"] = scope
        response = self.post_request("/oauth2/token", data=data)
        self.assertEqual(response.status_code, 200)
        return self.env["oauth.provider.token"].search(
            [("client_id", "=", self.client.id)], order="id DESC", limit=1
        )

    def test_token_without_scope_takes_code_scopes(self):
        """A token asked without scope gets the scopes granted to the code"""
        code = self.new_code()
        token = self._request_token_with_code(code)
        self.assertEqual(code.scope_ids, self.client.scope_ids[0])
        self.assertEqual(token.scope_ids, code.scope_ids)

    def test_token_cannot_extend_code_scopes(self):
        """A token can not get more scopes than the ones granted to the code"""
        code = self.new_code()
        token = self._request_token_with_code(
            code, scope=" ".join(self.client.scope_ids.mapped("code"))
        )
        self.assertEqual(token.scope_ids, code.scope_ids)

    def test_resources_with_valid_token(self):
        """Call /oauth2/resources/<model> with a valid Bearer token"""
        token = self.new_token()
        token.scope_ids = self.client.scope_ids
        response = self.get_request(
            "/oauth2/resources/res.users",
            headers={"Authorization": f"Bearer {token.token}"},
        )
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.data.decode("utf8"))
        self.assertEqual(response_data["resource"], "res.users")
        self.assertEqual(
            response_data["data"][str(self.user.id)]["email"], self.user.email
        )

    def test_resources_without_token(self):
        """Call /oauth2/resources/<model> without token"""
        response = self.get_request("/oauth2/resources/res.users")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(
            json.loads(response.data.decode("utf8")),
            {"error": "invalid_or_expired_token"},
        )

    def test_resources_with_expired_token(self):
        """Call /oauth2/resources/<model> with an expired token"""
        token = self.new_token()
        token.scope_ids = self.client.scope_ids
        token.expires_at = fields.Datetime.subtract(fields.Datetime.now(), hours=1)
        response = self.get_request(
            "/oauth2/resources/res.users",
            headers={"Authorization": f"Bearer {token.token}"},
        )
        self.assertEqual(response.status_code, 401)
