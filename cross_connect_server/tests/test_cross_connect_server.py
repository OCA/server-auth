# Copyright 2024 Akretion (http://www.akretion.com).
# @author Florian Mounier <florian.mounier@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo.http import root
from odoo.tests.common import RecordCapturer, tagged

from odoo.addons.extendable_fastapi.tests.common import FastAPITransactionCase

from ..routers import cross_connect_router


@tagged("post_install", "-at_install")
class TestCrossConnectServer(FastAPITransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.endpoint = cls.env["fastapi.endpoint"].create(
            {
                "name": "Cross Connect Server Endpoint",
                "root_path": "/api",
                "app": "cross_connect",
            }
        )
        cls.available_groups = (
            cls.env.ref("base.group_user")
            | cls.env.ref("fastapi.group_fastapi_user")
            | cls.env.ref("fastapi.group_fastapi_manager")
        )

        cls.endpoint.cross_connect_allowed_group_ids = cls.available_groups

        cls.client = cls.env["cross.connect.client"].create(
            {
                "name": "Test Client",
                "endpoint_id": cls.endpoint.id,
                "api_key": "server-api-key",
                "group_ids": [
                    (
                        6,
                        0,
                        (
                            cls.available_groups
                            - cls.env.ref("fastapi.group_fastapi_manager")
                        ).ids,
                    )
                ],
            }
        )

        cls.other_client = cls.env["cross.connect.client"].create(
            {
                "name": "Other Test Client",
                "endpoint_id": cls.endpoint.id,
                "api_key": "other-server-api-key",
                "group_ids": [
                    (
                        6,
                        0,
                        (cls.available_groups - cls.env.ref("base.group_user")).ids,
                    )
                ],
            }
        )

        cls.endpoint_user = cls.env["res.users"].create(
            {
                "name": "FastAPI Endpoint User",
                "login": "fastapi_endpoint_user",
                "groups_id": [
                    (6, 0, [cls.env.ref("fastapi.group_fastapi_endpoint_runner").id])
                ],
            }
        )

        cls.endpoint._handle_registry_sync(cls.endpoint.ids)

        cls.default_fastapi_running_user = cls.endpoint_user
        cls.default_fastapi_router = cross_connect_router
        cls.default_fastapi_app = cls.endpoint._get_app()
        cls.default_fastapi_dependency_overrides = (
            cls.default_fastapi_app.dependency_overrides
        )
        cls.default_fastapi_app.exception_handlers = {}

    def test_base(self):
        self.assertTrue(self.endpoint.cross_connect_secret_key)
        self.assertEqual(len(self.endpoint.cross_connect_client_ids), 2)
        self.assertFalse(self.endpoint.save_http_session)
        self.assertFalse(self.client.user_ids)

    def test_sync_ok(self):
        with self._create_test_client() as test_client:
            response = test_client.get(
                "/cross_connect/sync", headers={"api-key": "server-api-key"}
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "groups": [
                    {
                        "id": self.env.ref("base.group_user").id,
                        "name": "User types / Internal User",
                        "comment": None,
                    },
                    {
                        "id": self.env.ref("fastapi.group_fastapi_user").id,
                        "name": "FastAPI / User",
                        "comment": None,
                    },
                ]
            },
        )

    def test_sync_other(self):
        with self._create_test_client() as test_client:
            response = test_client.get(
                "/cross_connect/sync", headers={"api-key": "other-server-api-key"}
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "groups": [
                    {
                        "id": self.env.ref("fastapi.group_fastapi_manager").id,
                        "name": "FastAPI / Administrator",
                        "comment": None,
                    },
                    {
                        "id": self.env.ref("fastapi.group_fastapi_user").id,
                        "name": "FastAPI / User",
                        "comment": None,
                    },
                ]
            },
        )

    def test_sync_401(self):
        with self._create_test_client(raise_server_exceptions=False) as test_client:
            response = test_client.get(
                "/cross_connect/sync", headers={"api-key": "wrong-api-key"}
            )
            self.assertEqual(response.status_code, 401)

    def test_access_ok(self):
        with RecordCapturer(self.env["res.users"], []) as rc:
            with self._create_test_client() as test_client:
                response = test_client.post(
                    "/cross_connect/access",
                    headers={"api-key": "server-api-key"},
                    json={
                        "id": 12,
                        "name": "Client User",
                        "login": "user@client.example.org",
                        "email": "user@client.example.org",
                        "lang": "en_US",
                        "groups": [
                            self.env.ref("base.group_user").id,
                        ],
                    },
                )

        self.assertEqual(response.status_code, 200)
        json = response.json()
        self.assertEqual(json["client_id"], self.client.id)
        self.assertTrue(json["token"])

        self.assertEqual(len(rc.records), 1)
        new_user = rc.records[0]
        self.assertEqual(new_user.name, "Client User")
        self.assertEqual(new_user.login, f"{self.client.id}_12_user@client.example.org")
        self.assertEqual(new_user.email, "user@client.example.org")
        self.assertEqual(new_user.lang, "en_US")
        self.assertEqual(new_user.cross_connect_client_id.id, self.client.id)
        self.assertEqual(new_user.cross_connect_client_user_id, 12)
        self.assertIn(
            self.env.ref("base.group_user"),
            new_user.groups_id,
        )
        self.assertNotIn(self.env.ref("fastapi.group_fastapi_user"), new_user.groups_id)
        self.assertNotIn(
            self.env.ref("fastapi.group_fastapi_manager"), new_user.groups_id
        )

    def test_access_401(self):
        with RecordCapturer(self.env["res.users"], []) as rc:
            with self._create_test_client(raise_server_exceptions=False) as test_client:
                response = test_client.post(
                    "/cross_connect/access",
                    headers={"api-key": "wrong-api-key"},
                    json={
                        "id": 12,
                        "name": "Client User",
                        "login": "user@client.example.org",
                        "email": "user@client.example.org",
                        "lang": "en_US",
                        "groups": [
                            self.env.ref("base.group_user").id,
                        ],
                    },
                )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(len(rc.records), 0)

    def test_access_wrong_groups(self):
        with RecordCapturer(self.env["res.users"], []) as rc:
            with self._create_test_client(raise_server_exceptions=False) as test_client:
                response = test_client.post(
                    "/cross_connect/access",
                    headers={"api-key": "wrong-api-key"},
                    json={
                        "id": 12,
                        "name": "Client User",
                        "login": "user@client.example.org",
                        "email": "user@client.example.org",
                        "lang": "en_US",
                        "groups": [
                            self.env.ref("fastapi.group_fastapi_manager").id,
                        ],
                    },
                )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(len(rc.records), 0)

    def test_access_existing(self):
        with RecordCapturer(self.env["res.users"], []) as rc:
            with self._create_test_client() as test_client:
                response = test_client.post(
                    "/cross_connect/access",
                    headers={"api-key": "server-api-key"},
                    json={
                        "id": 12,
                        "name": "Client User",
                        "login": "user@client.example.org",
                        "email": "user@client.example.org",
                        "lang": "en_US",
                        "groups": [
                            self.env.ref("base.group_user").id,
                        ],
                    },
                )
            self.assertEqual(response.status_code, 200)

        with RecordCapturer(self.env["res.users"], []) as rc2:
            with self._create_test_client() as test_client:
                response = test_client.post(
                    "/cross_connect/access",
                    headers={"api-key": "server-api-key"},
                    json={
                        "id": 12,
                        "name": "Client User2",
                        "login": "user2@client.example.org",
                        "email": "user2@client.example.org",
                        "lang": "en_US",
                        "groups": [
                            self.env.ref("fastapi.group_fastapi_user").id,
                        ],
                    },
                )

        self.assertEqual(response.status_code, 200)
        json = response.json()
        self.assertEqual(json["client_id"], self.client.id)
        self.assertTrue(json["token"])

        self.assertEqual(len(rc.records), 1)
        self.assertEqual(len(rc2.records), 0)
        new_user = rc.records[0]
        self.assertEqual(new_user.name, "Client User2")
        self.assertEqual(
            new_user.login, f"{self.client.id}_12_user2@client.example.org"
        )
        self.assertEqual(new_user.email, "user2@client.example.org")
        self.assertEqual(new_user.lang, "en_US")
        self.assertIn(self.env.ref("fastapi.group_fastapi_user"), new_user.groups_id)
        self.assertNotIn(
            self.env.ref("fastapi.group_fastapi_manager"), new_user.groups_id
        )

    def test_login_ok(self):
        with RecordCapturer(self.env["res.users"], []) as rc:
            with self._create_test_client() as test_client:
                response = test_client.post(
                    "/cross_connect/access",
                    headers={"api-key": "server-api-key"},
                    json={
                        "id": 12,
                        "name": "Client User",
                        "login": "user@client.example.org",
                        "email": "user@client.example.org",
                        "lang": "en_US",
                        "groups": [
                            self.env.ref("base.group_user").id,
                        ],
                    },
                )
            self.assertEqual(response.status_code, 200)

        new_user = rc.records[0]

        json = response.json()

        with self._create_test_client() as test_client:
            response = test_client.get(
                f"/cross_connect/login/{json['client_id']}/{json['token']}",
                follow_redirects=False,
            )

        self.assertEqual(response.status_code, 307)
        self.assertEqual(response.headers["location"], "/web")
        self.assertIn("session_id", response.cookies)
        self.assertEqual(
            root.session_store.get(response.cookies["session_id"]).get("uid"),
            new_user.id,
        )

    def test_login_wrong_client(self):
        with self._create_test_client() as test_client:
            response = test_client.post(
                "/cross_connect/access",
                headers={"api-key": "server-api-key"},
                json={
                    "id": 12,
                    "name": "Client User",
                    "login": "user@client.example.org",
                    "email": "user@client.example.org",
                    "lang": "en_US",
                    "groups": [
                        self.env.ref("base.group_user").id,
                    ],
                },
            )
        self.assertEqual(response.status_code, 200)

        json = response.json()

        with self._create_test_client(raise_server_exceptions=False) as test_client:
            response = test_client.get(
                f"/cross_connect/login/{self.other_client.id}/{json['token']}",
                follow_redirects=False,
            )

        self.assertEqual(response.status_code, 403)

    def test_login_wrong_token(self):
        with self._create_test_client() as test_client:
            response = test_client.post(
                "/cross_connect/access",
                headers={"api-key": "server-api-key"},
                json={
                    "id": 12,
                    "name": "Client User",
                    "login": "user@client.example.org",
                    "email": "user@client.example.org",
                    "lang": "en_US",
                    "groups": [
                        self.env.ref("base.group_user").id,
                    ],
                },
            )
        self.assertEqual(response.status_code, 200)

        json = response.json()

        with self._create_test_client(raise_server_exceptions=False) as test_client:
            response = test_client.get(
                f"/cross_connect/login/{json['client_id']}/wrong-token",
                follow_redirects=False,
            )

        self.assertEqual(response.status_code, 403)
