import responses

from odoo.tests import common


class TestOIDCDiscovery(common.HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.response_json = {
            "issuer": "http://localhost:8080/auth/realms/master",
            "authorization_endpoint": "http://localhost:8080/auth/realms/master/protocol/openid-connect/auth",
            "token_endpoint": "http://localhost:8080/auth/realms/master/protocol/openid-connect/token",
            "introspection_endpoint": "http://localhost:8080/auth/realms/master/protocol/openid-connect/token/introspect",
            "userinfo_endpoint": "http://localhost:8080/auth/realms/master/protocol/openid-connect/userinfo",
            "end_session_endpoint": "http://localhost:8080/auth/realms/master/protocol/openid-connect/logout",
            "jwks_uri": "http://localhost:8080/auth/realms/master/protocol/openid-connect/certs",
            "scopes_supported": [
                "openid",
                "address",
                "email",
                "microprofile-jwt",
                "offline_access",
                "phone",
                "profile",
                "roles",
                "web-origins",
                "user:*",
            ],
        }
        cls.provider = cls.env["auth.oauth.provider"].create(
            {
                "name": "Test OIDC Provider",
                "body": "Log in with Test OIDC Provider",
                "supports_oidc_discovery": True,
                "oidc_discovery_url": "http://localhost:8080/auth/realms/master/.well-known/openid-configuration",
            }
        )

    @responses.activate
    def test_oidc_discovery(self):
        responses.add(
            responses.GET,
            "http://localhost:8080/auth/realms/master/.well-known/openid-configuration",
            json=self.response_json,
        )
        self.provider.action_get_oidc_configuration()
        self.assertEqual(
            self.provider.auth_endpoint, self.response_json["authorization_endpoint"]
        )

    @responses.activate
    def test_oidc_scopes(self):
        responses.add(
            responses.GET,
            "http://localhost:8080/auth/realms/master/.well-known/openid-configuration",
            json=self.response_json,
        )
        self.provider.action_get_oidc_configuration()
        self.provider.scope = "openid profile email address phone fake_scope"
        res = self.provider.onchange_scope()
        self.assertIsInstance(res, dict)
        self.assertIn("warning", res)
        self.provider.scope = "openid profile email address phone user:test"
        res = self.provider.onchange_scope()
        self.assertEqual(res, None)
        self.provider.scope = "openid profile email address phone fake_scope:test"
        res = self.provider.onchange_scope()
        self.assertIsInstance(res, dict)
        self.assertIn("warning", res)
