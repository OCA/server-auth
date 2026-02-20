# Copyright 2018 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import base64

import responses

import odoo.tests.common as common


class TestKeycloakBase(common.SavepointCase):

    base_auth_url = "https://keycloak/auth"
    base_openid_url = base_auth_url + "/realms/Odoo/protocol/openid-connect"

    @classmethod
    def setUpClass(cls):
        super(TestKeycloakBase, cls).setUpClass()
        cls.env = cls.env(
            context=dict(cls.env.context, tracking_disable=True, no_reset_password=True)
        )
        cls.provider = cls.env["auth.oauth.provider"].create(
            {
                "name": "Keycloak",
                "client_id": "odoo",
                "client_secret": "c35a795e-65ef-432d-97fb-6ef4bea84bb8",
                "auth_endpoint": cls.base_openid_url + "/token",
                "validation_endpoint": cls.base_openid_url + "/token/introspect",
                "body": "foo",
                "enabled": True,
            }
        )

    def _assert_request_auth_header(self, request):
        """Validate request has basic auth header."""
        auth = request.headers["Authorization"].replace("Basic ", "")
        self.assertEqual(
            base64.decodebytes(auth.encode()),
            "{}:{}".format(
                self.provider.client_id, self.provider.client_secret
            ).encode(),
        )


FAKE_TOKEN_RESPONSE = {
    "session_state": "623c9060-fd20-40e1-ad31-090bd77d521e",
    "not-before-policy": 0,
    "expires_in": 60,
    "token_type": "bearer",
    "refresh_expires_in": 1800,
    "scope": "profile email",
    "access_token": base64.encodebytes(b"my nice token").decode("utf-8"),
    "refresh_token": base64.encodebytes(b"my nice refresh token").decode(
        "utf-8"
    ),
}
FAKE_USERS_RESPONSE = [
    {
        "username": "jdoe",
        "access": {
            "manage": True,
            "manageGroupMembership": True,
            "impersonate": True,
            "mapRoles": True,
            "view": True,
        },
        "notBefore": 0,
        "email": "john@doe.com",
        "emailVerified": False,
        "enabled": True,
        "createdTimestamp": 1539857662328,
        "totp": False,
        "disableableCredentialTypes": ["password"],
        "requiredActions": [],
        "id": "ef1d2e5d-1aad-4daf-858e-f246168a10ef",
    },
    {
        "username": "dduck",
        "access": {
            "manage": True,
            "manageGroupMembership": True,
            "impersonate": True,
            "mapRoles": True,
            "view": True,
        },
        "firstName": "Donald",
        "lastName": "Duck",
        "notBefore": 0,
        "emailVerified": False,
        "requiredActions": [],
        "enabled": True,
        "email": "donald@duck.com",
        "createdTimestamp": 1539871348882,
        "totp": False,
        "disableableCredentialTypes": [],
        "id": "1feb89e6-76bd-44a1-ab5d-df28b6477e19",
    },
]


class TestKeycloakWizBase(TestKeycloakBase):

    wiz_model = ""

    @classmethod
    def setUpClass(cls):
        super(TestKeycloakWizBase, cls).setUpClass()
        cls.users_endpoint = cls.base_auth_url + "/admin/realms/Odoo/users"
        cls.provider.update(
            {
                "users_endpoint": cls.users_endpoint,
                "superuser": "admin",
                "superuser_pwd": 'well, yes, is "admin"',
            }
        )
        cls.wiz = cls.env[cls.wiz_model].create(
            {
                "provider_id": cls.provider.id,
            }
        )
        # create users matching keycloak response
        cls.user_john = cls.env["res.users"].create(
            {
                "name": "John Doe",
                "login": "jdoe",
                "email": "john@doe.com",
            }
        )
        cls.user_donald = cls.env["res.users"].create(
            {
                "name": "Donald Duck",
                "login": "dduck",
                "email": "donald@duck.com",
            }
        )

    def setUp(self):
        super(TestKeycloakWizBase, self).setUp()
        responses.add(
            responses.POST,
            self.provider.auth_endpoint,
            json=FAKE_TOKEN_RESPONSE,
            status=200,
            content_type="application/json",
        )
