# Copyright 2026 Lorenzo Battistini
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import base64
import json
import re
from urllib.parse import parse_qs, urlencode, urlsplit

from odoo.tests.common import HttpCase, tagged

from . import common

CSRF_RE = re.compile(r'name="csrf_token"\s+value="([^"]+)"')
CONSENT_RE = re.compile(r'name="consent"\s+value="([^"]+)"')


def query_of(url):
    return {key: values[0] for key, values in parse_qs(urlsplit(url).query).items()}


@tagged("post_install", "-at_install")
class TestControllers(common.OAuthServerMixin, HttpCase):
    """The endpoints, called over HTTP as clients and browsers do."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.setup_oauth_server()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def url_open(self, *args, **kwargs):
        # the server shares the test cursor but not the test's cache
        self.env.flush_all()
        response = super().url_open(*args, **kwargs)
        self.env.invalidate_all()
        return response

    def get_json(self, path, status=200):
        response = self.url_open(path)
        self.assertEqual(response.status_code, status, response.text)
        return response

    def post(self, path, data=None, headers=None):
        return self.url_open(path, data=data, headers=headers, allow_redirects=False)

    def authorize_query(self, client=None, **params):
        """Query of an authorization request; returns (verifier, query)."""
        verifier, challenge = common.pkce_pair()
        query = dict(
            {
                "client_id": (client or self.client).identifier,
                "redirect_uri": common.REDIRECT_URI,
                "response_type": "code",
                "code_challenge": challenge,
                "code_challenge_method": "S256",
                "resource": self.resource.uri,
                "scope": "read",
                "state": "xyz",
            },
            **params
        )
        return verifier, {key: value for key, value in query.items() if value}

    def open_authorize(self, query):
        return self.url_open(
            "/oauth/authorize?" + urlencode(query), allow_redirects=False
        )

    def consent_form(self, query):
        """GET the consent page; returns (csrf_token, consent)."""
        response = self.open_authorize(query)
        self.assertEqual(response.status_code, 200, response.text)
        return CSRF_RE.search(response.text).group(1), CONSENT_RE.search(
            response.text
        ).group(1)

    def decide(self, csrf_token, consent, decision="approve"):
        return self.post(
            "/oauth/authorize/decision",
            {"csrf_token": csrf_token, "consent": consent, "decision": decision},
        )

    def token_request(self, data, headers=None):
        return self.post("/oauth/token", data, headers)

    # ------------------------------------------------------------------
    # Metadata
    # ------------------------------------------------------------------

    def test_authorization_server_metadata(self):
        response = self.get_json("/.well-known/oauth-authorization-server")
        self.assertEqual(response.headers.get("Access-Control-Allow-Origin"), "*")
        metadata = response.json()
        self.assertEqual(metadata["issuer"], common.ISSUER)
        self.assertEqual(
            metadata["authorization_endpoint"], common.ISSUER + "/oauth/authorize"
        )
        self.assertEqual(metadata["token_endpoint"], common.ISSUER + "/oauth/token")
        self.assertEqual(
            metadata["registration_endpoint"], common.ISSUER + "/oauth/register"
        )
        self.assertEqual(metadata["code_challenge_methods_supported"], ["S256"])
        self.assertTrue(metadata["authorization_response_iss_parameter_supported"])
        self.assertTrue(metadata["client_id_metadata_document_supported"])
        self.assertTrue({"read", "write"} <= set(metadata["scopes_supported"]))
        self.env["ir.config_parameter"].sudo().set_param(
            "auth_oauth_server.dcr_enabled", False
        )
        metadata = self.get_json("/.well-known/oauth-authorization-server").json()
        self.assertNotIn("registration_endpoint", metadata)

    def test_protected_resource_metadata(self):
        metadata = self.get_json(
            "/.well-known/oauth-protected-resource/test_api"
        ).json()
        self.assertEqual(metadata, self.resource._metadata())
        self.get_json("/.well-known/oauth-protected-resource/unknown", 404)

    # ------------------------------------------------------------------
    # Authorization endpoint
    # ------------------------------------------------------------------

    def test_authorize_asks_to_log_in(self):
        _verifier, query = self.authorize_query()
        response = self.open_authorize(query)
        self.assertEqual(response.status_code, 303)
        location = response.headers["Location"]
        self.assertEqual(urlsplit(location).path, "/web/login")
        back = query_of(location)["redirect"]
        self.assertEqual(urlsplit(back).path, "/oauth/authorize")
        self.assertEqual(query_of(back), query)

    def test_authorization_code_flow(self):
        self.authenticate(self.user.login, self.user.login)
        verifier, query = self.authorize_query()
        response = self.open_authorize(query)
        self.assertEqual(response.headers["X-Frame-Options"], "DENY")
        self.assertIn(
            "frame-ancestors 'none'", response.headers["Content-Security-Policy"]
        )
        self.assertIn("Test App", response.text)
        self.assertIn("app.example.com", response.text)
        csrf_token, consent = self.consent_form(query)
        response = self.decide(csrf_token, consent)
        self.assertEqual(response.status_code, 303)
        location = response.headers["Location"]
        self.assertTrue(location.startswith(common.REDIRECT_URI + "?"), location)
        answer = query_of(location)
        self.assertEqual(answer["state"], "xyz")
        self.assertEqual(answer["iss"], common.ISSUER)
        response = self.token_request(
            {
                "grant_type": "authorization_code",
                "code": answer["code"],
                "code_verifier": verifier,
                "redirect_uri": common.REDIRECT_URI,
                "client_id": self.client.identifier,
                "resource": self.resource.uri,
            }
        )
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.headers["Cache-Control"], "no-store")
        tokens = response.json()
        self.assertEqual(tokens["scope"], "read")
        self.assertEqual(self.check_token(tokens["access_token"]), self.user.id)
        response = self.token_request(
            {
                "grant_type": "refresh_token",
                "refresh_token": tokens["refresh_token"],
                "client_id": self.client.identifier,
            }
        )
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(
            self.check_token(response.json()["access_token"]), self.user.id
        )

    def test_deny(self):
        self.authenticate(self.user.login, self.user.login)
        _verifier, query = self.authorize_query()
        response = self.decide(*self.consent_form(query), decision="deny")
        self.assertEqual(response.status_code, 303)
        answer = query_of(response.headers["Location"])
        self.assertEqual(answer["error"], "access_denied")
        self.assertEqual(answer["state"], "xyz")
        self.assertEqual(answer["iss"], common.ISSUER)
        self.assertNotIn("code", answer)

    def test_decision_is_bound_to_the_request(self):
        self.authenticate(self.user.login, self.user.login)
        _verifier, query = self.authorize_query()
        csrf_token, consent = self.consent_form(query)
        tampered = consent[:-1] + ("1" if consent.endswith("0") else "0")
        response = self.decide(csrf_token, tampered)
        self.assertEqual(response.status_code, 400)
        self.assertNotIn("Location", response.headers)
        # another user cannot use it
        self.authenticate(self.other_user.login, self.other_user.login)
        other_csrf_token, _consent = self.consent_form(query)
        response = self.decide(other_csrf_token, consent)
        self.assertEqual(response.status_code, 400)
        self.assertFalse(
            self.env["oauth.server.authorization"].search(
                [("client_id", "=", self.client.id)]
            )
        )

    def test_authorize_errors(self):
        self.authenticate(self.user.login, self.user.login)
        # the redirect URI is not trusted: show the error, never redirect
        _verifier, query = self.authorize_query(
            redirect_uri="https://evil.example.com/callback"
        )
        response = self.open_authorize(query)
        self.assertEqual(response.status_code, 400)
        self.assertNotIn("Location", response.headers)
        # a client registered by an administrator gets the error back
        _verifier, query = self.authorize_query(code_challenge_method="plain")
        response = self.open_authorize(query)
        self.assertEqual(response.status_code, 303)
        answer = query_of(response.headers["Location"])
        self.assertEqual(answer["error"], "invalid_request")
        self.assertEqual(answer["state"], "xyz")
        # a self-registered one does not, its redirect URI may be anyone's
        registered = self.env["oauth.server.client"]._register_dynamic(
            {
                "redirect_uris": [common.REDIRECT_URI],
                "token_endpoint_auth_method": "none",
            }
        )
        client = self.env["oauth.server.client"].search(
            [("identifier", "=", registered["client_id"])]
        )
        _verifier, query = self.authorize_query(
            client=client, code_challenge_method="plain"
        )
        response = self.open_authorize(query)
        self.assertEqual(response.status_code, 400)
        self.assertNotIn("Location", response.headers)

    # ------------------------------------------------------------------
    # Token and revocation endpoints
    # ------------------------------------------------------------------

    def test_token_errors(self):
        response = self.token_request(
            {"grant_type": "authorization_code", "client_id": "unknown"}
        )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["error"], "invalid_client")
        self.assertIn("Basic", response.headers["WWW-Authenticate"])
        response = self.token_request(
            {"grant_type": "password", "client_id": self.client.identifier}
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "unsupported_grant_type")
        response = self.token_request(
            {
                "grant_type": "authorization_code",
                "code": "unknown",
                "client_id": self.client.identifier,
            }
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "invalid_grant")

    def test_code_reuse_revokes_over_http(self):
        """The revocation done before answering the error is kept."""
        authorization, code, verifier = self.approve()
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "code_verifier": verifier,
            "client_id": self.client.identifier,
        }
        self.assertEqual(self.token_request(data).status_code, 200)
        self.assertEqual(self.token_request(data).status_code, 400)
        self.assertTrue(authorization.revoked)

    def test_confidential_client_basic_auth(self):
        client = self.confidential_client
        _authorization, code, verifier = self.approve(client=client)
        credentials = "%s:%s" % (client.identifier, self.client_secret)
        response = self.token_request(
            {
                "grant_type": "authorization_code",
                "code": code,
                "code_verifier": verifier,
            },
            headers={
                "Authorization": "Basic "
                + base64.b64encode(credentials.encode()).decode()
            },
        )
        self.assertEqual(response.status_code, 200, response.text)

    def test_revoke(self):
        authorization, tokens = self.tokens()
        response = self.post(
            "/oauth/revoke",
            {"token": tokens["refresh_token"], "client_id": self.client.identifier},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(authorization.revoked)
        response = self.post(
            "/oauth/revoke", {"token": "unknown", "client_id": self.client.identifier}
        )
        self.assertEqual(response.status_code, 200)
        response = self.post("/oauth/revoke", {"token": "x", "client_id": "unknown"})
        self.assertEqual(response.status_code, 401)

    def test_cors_preflight(self):
        response = self.opener.options(
            self.base_url() + "/oauth/token",
            headers={
                "Origin": "https://inspector.example.com",
                "Access-Control-Request-Method": "POST",
            },
        )
        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.headers["Access-Control-Allow-Origin"], "*")

    # ------------------------------------------------------------------
    # Registration endpoint
    # ------------------------------------------------------------------

    def register(self, body):
        return self.post(
            "/oauth/register", body, headers={"Content-Type": "application/json"}
        )

    def test_register(self):
        response = self.register(
            json.dumps(
                {
                    "client_name": "MCP Client",
                    "redirect_uris": ["http://localhost:6274/callback"],
                    "token_endpoint_auth_method": "none",
                }
            )
        )
        self.assertEqual(response.status_code, 201, response.text)
        client_id = response.json()["client_id"]
        self.assertTrue(
            self.env["oauth.server.client"].search([("identifier", "=", client_id)])
        )
        response = self.register("not json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "invalid_client_metadata")
        response = self.register(json.dumps({"client_name": "x" * 20000}))
        self.assertEqual(response.status_code, 400)
        self.env["ir.config_parameter"].sudo().set_param(
            "auth_oauth_server.dcr_enabled", False
        )
        response = self.register(json.dumps({"redirect_uris": [common.REDIRECT_URI]}))
        self.assertEqual(response.status_code, 404)
