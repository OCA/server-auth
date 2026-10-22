# Copyright 2016 SYLEAM
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import hashlib
import json
import logging
from urllib.parse import parse_qs, urlparse

from odoo import fields

_logger = logging.getLogger(__name__)


class TestOAuthProviderAurhorizeController:
    def test_authorize_error_missing_arguments(self):
        """Call /oauth2/authorize without any argument

        Must return an unknown client identifier error
        """
        self.login(self.user.login, self.user_password)
        response = self.get_request("/oauth2/authorize")
        self.assertEqual(response.status_code, 200)
        response_text = response.data.decode("utf8")
        self.assertTrue("Unknown Client Identifier!" in response_text)
        self.assertTrue("This client identifier is invalid." in response_text)

    def test_authorize_error_invalid_request(self):
        """Call /oauth2/authorize with only the client_id argument

        Must return an invalid_request error
        """
        self.login(self.user.login, self.user_password)
        response = self.get_request(
            "/oauth2/authorize",
            data={
                "client_id": self.client.identifier,
            },
        )
        self.assertEqual(response.status_code, 200)
        response_text = response.data.decode("utf8")
        self.assertTrue("Error: invalid_request" in response_text)
        self.assertTrue(
            "An unknown error occured! Please contact your "
            "administrator" in response_text
        )

    def test_authorize_error_unsupported_response_type(self):
        """Call /oauth2/authorize with an unsupported response type

        Must return an unsupported_response_type error
        """
        self.login(self.user.login, self.user_password)
        response = self.get_request(
            "/oauth2/authorize",
            data={
                "client_id": self.client.identifier,
                "response_type": "wrong response type",
            },
        )
        self.assertEqual(response.status_code, 200)
        response_text = response.data.decode("utf8")
        self.assertTrue("Error: unsupported_response_type" in response_text)
        self.assertTrue(
            "An unknown error occured! Please contact your "
            "administrator" in response_text
        )

    def test_authorize_error_wrong_scopes(self):
        """Call /oauth2/authorize with wrong scopes

        Must return an invalid_scope error
        """
        self.login(self.user.login, self.user_password)
        response = self.get_request(
            "/oauth2/authorize",
            data={
                "client_id": self.client.identifier,
                "response_type": self.client.response_type,
                "scope": "wrong scope",
            },
        )
        self.assertEqual(response.status_code, 200)
        response_text = response.data.decode("utf8")
        self.assertTrue("Error: invalid_scope" in response_text)
        self.assertTrue(
            "An unknown error occured! Please contact your "
            "administrator" in response_text
        )

    def test_authorize_error_wrong_uri(self):
        """Call the authorize method with a wrong redirect_uri

        Must return an invalid_request error
        """
        self.login(self.user.login, self.user_password)
        response = self.get_request(
            "/oauth2/authorize",
            data={
                "client_id": self.client.identifier,
                "response_type": self.client.response_type,
                "redirect_uri": "http://wrong.redirect.uri",
            },
        )
        self.assertEqual(response.status_code, 200)
        response_text = response.data.decode("utf8")
        self.assertTrue("Error: invalid_request" in response_text)
        self.assertTrue("Mismatching redirect URI" in response_text)

    def test_authorize_error_missing_uri(self):
        """Call /oauth2/authorize without any configured redirect URI

        Must return an invalid_request error
        """
        self.client.redirect_uri_ids.unlink()
        self.login(self.user.login, self.user_password)
        response = self.get_request(
            "/oauth2/authorize",
            data={
                "client_id": self.client.identifier,
                "response_type": self.client.response_type,
                "scope": self.client.scope_ids[0].code,
            },
        )
        self.assertEqual(response.status_code, 200)
        response_text = response.data.decode("utf8")
        self.assertTrue("Error: invalid_request" in response_text)
        self.assertTrue("Missing redirect URI." in response_text)

    def test_authorize_post_errors(self):
        """Call /oauth2/authorize in POST without any session

        Must return an unknown client identifier error
        """
        self.login(self.user.login, self.user_password)
        response = self.post_request("/oauth2/authorize")
        self.assertEqual(response.status_code, 200)
        response_text = response.data.decode("utf8")
        self.assertTrue("Unknown Client Identifier!" in response_text)
        self.assertTrue("This client identifier is invalid." in response_text)

    def test_authorize_unsafe_chars(self):
        """Unsafe chars in the state come back unchanged to the client"""
        state = "a{b}|c^d <e>"
        self.login(self.user.login, self.user_password)
        response = self.get_request(
            "/oauth2/authorize",
            data={
                "client_id": self.client.identifier,
                "response_type": self.client.response_type,
                "redirect_uri": self.redirect_uri_base,
                "state": state,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.client.name, response.data.decode("utf8"))
        response = self.post_request("/oauth2/authorize")
        self.assertEqual(response.status_code, 302)
        location = urlparse(response.headers["Location"])
        params = parse_qs(location.query or location.fragment)
        self.assertEqual(params["state"], [state])


class TestOAuthProviderRefreshTokenController:
    def test_refresh_token_error_too_much_scopes(self):
        """Call /oauth2/token using a refresh token, with too much scopes"""
        token = self.new_token()
        response = self.post_request(
            "/oauth2/token",
            data={
                "client_id": self.client.identifier,
                "scope": self.client.scope_ids.mapped("code"),
                "grant_type": "refresh_token",
                "refresh_token": token.refresh_token,
            },
        )
        self.assertEqual(response.status_code, 400)
        response_text = response.data.decode("utf8")
        self.assertEqual(json.loads(response_text), {"error": "invalid_scope"})

    def test_refresh_token(self):
        """Get a new token using the refresh token"""
        token = self.new_token()
        token.scope_ids = self.client.scope_ids[0]
        response = self.post_request(
            "/oauth2/token",
            data={
                "client_id": self.client.identifier,
                "scope": " ".join(token.scope_ids.mapped("code")),
                "grant_type": "refresh_token",
                "refresh_token": token.refresh_token,
            },
        )
        response_text = response.data.decode("utf8")
        response_data = json.loads(response_text)
        # A new token should have been generated
        # We can safely pick the latest generated token here, because no other
        # token could have been generated during the test
        new_token = self.env["oauth.provider.token"].search(
            [("client_id", "=", self.client.id)], order="id DESC", limit=1
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(new_token.token, response_data["access_token"])
        self.assertEqual(new_token.token_type, response_data["token_type"])
        self.assertEqual(new_token.refresh_token, response_data["refresh_token"])
        self.assertEqual(new_token.scope_ids, token.scope_ids)
        self.assertEqual(new_token.user_id, self.user)
        self.assertNotIn("odoo_user_id", response_data)

    def test_refresh_token_with_expired_access_token(self):
        """The refresh token still works once its access token expired"""
        token = self.new_token()
        token.scope_ids = self.client.scope_ids[0]
        token.expires_at = fields.Datetime.subtract(fields.Datetime.now(), hours=2)
        response = self.post_request(
            "/oauth2/token",
            data={
                "client_id": self.client.identifier,
                "grant_type": "refresh_token",
                "refresh_token": token.refresh_token,
            },
        )
        response_data = json.loads(response.data.decode("utf8"))
        self.assertEqual(response.status_code, 200)
        new_token = self.env["oauth.provider.token"].search(
            [("token", "=", response_data["access_token"])]
        )
        self.assertEqual(new_token.scope_ids, token.scope_ids)
        self.assertEqual(new_token.user_id, self.user)


class TestOAuthProviderTokeninfoController:
    def test_tokeninfo_long_lifetime(self):
        """expires_in counts the whole lifetime, days included"""
        token = self.new_token()
        token.expires_at = fields.Datetime.add(fields.Datetime.now(), days=2)
        response = self.get_request(
            "/oauth2/tokeninfo", data={"access_token": token.token}
        )
        response_data = json.loads(response.data.decode("utf8"))
        self.assertEqual(response.status_code, 200)
        self.assertGreater(response_data["expires_in"], 86400)

    def test_tokeninfo_error_missing_arguments(self):
        """Call /oauth2/tokeninfo without any argument

        Must retun an invalid_or_expired_token error
        """
        response = self.get_request("/oauth2/tokeninfo")
        self.assertEqual(response.status_code, 401)
        response_text = response.data.decode("utf8")
        self.assertEqual(
            json.loads(response_text), {"error": "invalid_or_expired_token"}
        )

    def test_tokeninfo(self):
        """Retrieve token information"""
        token = self.new_token()
        token.scope_ids = self.client.scope_ids[0]
        response = self.get_request(
            "/oauth2/tokeninfo",
            data={
                "access_token": token.token,
            },
        )
        token_lifetime = (token.expires_at - fields.Datetime.now()).total_seconds()
        response_text = response.data.decode("utf8")
        response_data = json.loads(response_text)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response_data["audience"], token.client_id.identifier)
        self.assertEqual(
            response_data["scopes"], " ".join(token.scope_ids.mapped("code"))
        )
        # Test a range because the test might not be accurate, depending on the
        # test system load
        self.assertTrue(
            token_lifetime - 5 < response_data["expires_in"] < token_lifetime + 5
        )
        self.assertEqual(
            response_data["user_id"],
            hashlib.sha256(
                (token.client_id.identifier + token.user_id.oauth_identifier).encode(
                    "utf8"
                )
            ).hexdigest(),
        )

    def test_tokeninfo_without_scopes(self):
        """Call /oauth2/tokeninfo without any scope

        Retrieve token information without any scopes on the token
        The user_id field should not be included
        """
        token = self.new_token()
        token.scope_ids = self.env["oauth.provider.scope"]
        response = self.get_request(
            "/oauth2/tokeninfo",
            data={
                "access_token": token.token,
            },
        )
        token_lifetime = (token.expires_at - fields.Datetime.now()).total_seconds()
        response_text = response.data.decode("utf8")
        response_data = json.loads(response_text)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response_data["audience"], token.client_id.identifier)
        self.assertEqual(
            response_data["scopes"], " ".join(token.scope_ids.mapped("code"))
        )
        # Test a range because the test might not be accurate, depending on the
        # test system load
        self.assertTrue(
            token_lifetime - 5 < response_data["expires_in"] < token_lifetime + 5
        )


class TestOAuthProviderUserinfoController:
    def test_userinfo_error_missing_arguments(self):
        """Call /oauth2/userinfo without any argument

        Must return an invalid_or_expired_token error
        """
        response = self.get_request("/oauth2/userinfo")
        response_text = response.data.decode("utf8")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(
            json.loads(response_text), {"error": "invalid_or_expired_token"}
        )

    def test_userinfo_single_scope(self):
        """Retrieve user information with only a single scope"""
        token = self.new_token()
        token.scope_ids = self.client.scope_ids[0]

        # Retrieve user information
        response = self.get_request(
            "/oauth2/userinfo",
            data={
                "access_token": token.token,
            },
        )
        response_text = response.data.decode("utf8")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            json.loads(response_text),
            {
                "id": self.user.id,
                "email": self.user.email,
            },
        )

    def test_userinfo_multiple_scope(self):
        """Retrieve user information with only a all test scopes"""
        token = self.new_token()
        token.scope_ids = self.client.scope_ids

        # Retrieve user information
        response = self.get_request(
            "/oauth2/userinfo",
            data={
                "access_token": token.token,
            },
        )
        response_text = response.data.decode("utf8")
        # The Email scope allows to read the email
        # The Profile scope allows to read the name and city
        # The id of the recod is always added (standard Odoo behaviour)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            json.loads(response_text),
            {
                "id": self.user.id,
                "name": self.user.name,
                "email": self.user.email,
                "city": self.user.city,
            },
        )


class TestOAuthProviderOtherinfoController:
    def _get_otherinfo(self, data=None):
        """Call the deprecated /oauth2/otherinfo endpoint"""
        with self.assertLogs("odoo.addons.oauth_provider.controllers.main", "WARNING"):
            return self.get_request("/oauth2/otherinfo", data=data)

    def _add_groups_scope(self, token):
        token.scope_ids += self.env["oauth.provider.scope"].create(
            {
                "name": "Groups",
                "code": "groups",
                "description": "List of accessible groups",
                "model_id": self.env.ref("base.model_res_groups").id,
                "filter_id": False,
                "field_ids": [
                    (6, 0, [self.env.ref("base.field_res_groups__name").id]),
                ],
            }
        )

    def test_otherinfo_error_missing_arguments(self):
        """Call /oauth2/otherinfo method without any argument

        Must return an invalid_request error
        """
        response = self._get_otherinfo()
        response_text = response.data.decode("utf8")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(json.loads(response_text)["error"], "invalid_request")

    def test_otherinfo_error_missing_model(self):
        """Call /oauth2/otherinfo method without the model argument

        Must return an invalid_request error
        """
        token = self.new_token()
        response = self._get_otherinfo(data={"access_token": token.token})
        response_text = response.data.decode("utf8")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(json.loads(response_text)["error"], "invalid_request")

    def test_otherinfo_error_invalid_model(self):
        """Call /oauth2/otherinfo method withan invalid model

        Must return an invalid_resource error
        """
        token = self.new_token()
        response = self._get_otherinfo(
            data={"access_token": token.token, "model": "invalid.model"},
        )
        response_text = response.data.decode("utf8")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(json.loads(response_text)["error"], "invalid_resource")

    def test_otherinfo_user_information(self):
        """Call /oauth2/otherinfo to retrieve information using the token"""
        token = self.new_token()
        token.scope_ids = self.client.scope_ids
        self._add_groups_scope(token)

        # Retrieve user information
        response = self._get_otherinfo(
            data={
                "access_token": token.token,
                "model": "res.users",
            },
        )
        response_text = response.data.decode("utf8")
        # The Email scope allows to read the email
        # The Profile scope allows to read the name and city
        # The id of the recod is always added (standard Odoo behaviour)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            json.loads(response_text),
            {
                "resource": "res.users",
                "data": {
                    str(self.user.id): {
                        "id": self.user.id,
                        "name": self.user.name,
                        "email": self.user.email,
                        "city": self.user.city,
                    }
                },
                "scope": "email profile",
                "client_id": self.client.identifier,
            },
        )

    def test_otherinfo_group_information(self):
        """Call /oauth2/otherinfo to retrieve information using the token"""
        token = self.new_token()
        token.scope_ids = self.client.scope_ids
        self._add_groups_scope(token)

        # Retrieve groups information
        all_groups = self.env["res.groups"].search([])
        response = self._get_otherinfo(
            data={
                "access_token": token.token,
                "model": "res.groups",
            },
        )
        response_text = response.data.decode("utf8")
        response_data = json.loads(response_text)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response_data["scope"], "groups")
        self.assertEqual(
            sorted(response_data["data"].keys()), sorted(map(str, all_groups.ids))
        )


class TestOAuthProviderRevokeTokenController:
    def test_revoke_token_error_missing_arguments(self):
        """Call /oauth2/revoke_token method without any argument"""
        response = self.post_request("/oauth2/revoke_token")
        response_text = response.data.decode("utf8")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(
            json.loads(response_text), {"error": "invalid_or_expired_token"}
        )

    def test_revoke_token_error_missing_client_id(self):
        """Call /oauth2/revoke_token method without client identifier"""
        token = self.new_token()
        response = self.post_request(
            "/oauth2/revoke_token",
            data={
                "token": token.token,
            },
        )
        response_text = response.data.decode("utf8")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(json.loads(response_text), {"error": "invalid_client"})

    def test_revoke_token_error_missing_token(self):
        """Call /oauth2/revoke_token method without token"""
        response = self.post_request(
            "/oauth2/revoke_token",
            data={
                "client_id": self.client.identifier,
            },
        )
        response_text = response.data.decode("utf8")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(
            json.loads(response_text), {"error": "invalid_or_expired_token"}
        )

    def test_revoke_access_token(self):
        """Revoke an access token"""
        token = self.new_token()
        self.post_request(
            "/oauth2/revoke_token",
            data={
                "client_id": self.client.identifier,
                "token": token.token,
            },
        )
        self.assertFalse(token.exists())

    def test_revoke_access_token_without_csrf(self):
        """An external client revokes a token without any CSRF token"""
        self.csrf_patcher.stop()
        token = self.new_token()
        response = self.post_request(
            "/oauth2/revoke_token",
            data={
                "client_id": self.client.identifier,
                "token": token.token,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(token.exists())

    def test_revoke_refresh_token(self):
        """Revoke a refresh token"""
        token = self.new_token()
        self.post_request(
            "/oauth2/revoke_token",
            data={
                "client_id": self.client.identifier,
                "token": token.refresh_token,
            },
        )
        self.assertTrue(token.exists())
        self.assertFalse(token.refresh_token)

    def test_revoke_refresh_token_with_expired_access_token(self):
        """The refresh token of an expired access token can be revoked"""
        token = self.new_token()
        token.expires_at = fields.Datetime.subtract(fields.Datetime.now(), hours=2)
        response = self.post_request(
            "/oauth2/revoke_token",
            data={
                "client_id": self.client.identifier,
                "token": token.refresh_token,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(token.with_context(active_test=False).refresh_token)
