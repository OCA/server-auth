# Copyright 2024 Akretion (http://www.akretion.com).
# @author Florian Mounier <florian.mounier@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from unittest.mock import Mock, patch

from odoo.exceptions import UserError
from odoo.tests.common import HttpCase, TransactionCase


def _mock_json(data):
    res = Mock()
    res.json = lambda: data
    return res


class TestCrossConnectClient(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.server = cls.env["cross.connect.server"].create(
            {
                "name": "Test Server",
                "server_url": "http://test-server.example.com",
                "api_key": "server-api-key",
            }
        )
        cls.env["cross.connect.server"].create(
            {
                "name": "Other Test Server",
                "server_url": "http://other-test-server.example.com",
                "api_key": "other-server-api-key",
            }
        )

    def test_base(self):
        self.assertFalse(self.server.group_ids)
        self.assertFalse(self.server.menu_id)
        self.assertFalse(self.server.web_icon_data)

    def test_absolute_url_for(self):
        self.assertEqual(
            self.server._absolute_url_for("test"),
            "http://test-server.example.com/cross_connect/test",
        )

        self.assertEqual(
            self.server._absolute_url_for("/test"),
            "http://test-server.example.com/cross_connect/test",
        )

        self.server.server_url = "http://test-server.example.com/"

        self.assertEqual(
            self.server._absolute_url_for("test"),
            "http://test-server.example.com/cross_connect/test",
        )

        self.assertEqual(
            self.server._absolute_url_for("/test"),
            "http://test-server.example.com/cross_connect/test",
        )

    def test_menu(self):
        self.assertFalse(self.server.menu_id)
        self.server.group_ids = [(0, 0, {"name": "Test Group"})]
        self.assertTrue(self.server.menu_id)
        self.server.web_icon_data = b"YQ=="
        self.assertEqual(self.server.menu_id.web_icon_data, b"YQ==")
        self.server.action_disable()
        self.assertFalse(self.server.menu_id)

    @patch("requests.request")
    def test_sync(self, req):
        req.return_value = _mock_json(
            {
                "groups": [
                    {"id": 1, "name": "Test Group 1", "comment": "Comment 1"},
                    {"id": 2, "name": "Test Group 2", "comment": "Comment 2"},
                ]
            }
        )

        self.server.action_sync()

        req.assert_called_once_with(
            "GET",
            "http://test-server.example.com/cross_connect/sync",
            headers={"api-key": "server-api-key"},
            json=None,
            timeout=10,
        )

        self.assertEqual(len(self.server.group_ids), 2)
        self.assertEqual(self.server.group_ids[0].name, "Test Server: Test Group 1")
        self.assertEqual(self.server.group_ids[0].comment, "Comment 1")
        self.assertEqual(self.server.group_ids[0].cross_connect_server_group_id, 1)

        self.assertEqual(self.server.group_ids[1].name, "Test Server: Test Group 2")
        self.assertEqual(self.server.group_ids[1].comment, "Comment 2")
        self.assertEqual(self.server.group_ids[1].cross_connect_server_group_id, 2)

        self.assertTrue(self.server.menu_id)
        self.assertEqual(self.server.menu_id.name, "Test Server")
        self.assertEqual(
            self.server.menu_id.web_icon,
            "cross_connect_client,static/description/web_icon_data.png",
        )
        self.assertEqual(self.server.menu_id.groups_id, self.server.group_ids)
        self.assertTrue(self.server.menu_id.action.name, "Test Server")
        self.assertEqual(
            self.server.menu_id.action.url, f"/cross_connect_server/{self.server.id}"
        )
        self.assertEqual(self.server.menu_id.action.target, "new")

        self.assertTrue(self.server.web_icon_data)

    @patch("requests.request")
    def test_successive_sync(self, req):
        req.return_value = _mock_json(
            {
                "groups": [
                    {"id": 1, "name": "Test Group 1", "comment": "Comment 1"},
                    {"id": 2, "name": "Test Group 2", "comment": "Comment 2"},
                ]
            }
        )

        self.server.action_sync()
        req.return_value = _mock_json(
            {
                "groups": [
                    {
                        "id": 2,
                        "name": "Test Group 2 edited",
                        "comment": "Comment edited 2",
                    },
                    {"id": 3, "name": "Test Group 3", "comment": "Comment 3"},
                ]
            }
        )

        self.server.action_sync()

        self.assertEqual(len(self.server.group_ids), 2)
        self.assertEqual(
            self.server.group_ids[0].name, "Test Server: Test Group 2 edited"
        )
        self.assertEqual(self.server.group_ids[0].comment, "Comment edited 2")
        self.assertEqual(self.server.group_ids[0].cross_connect_server_group_id, 2)

        self.assertEqual(self.server.group_ids[1].name, "Test Server: Test Group 3")
        self.assertEqual(self.server.group_ids[1].comment, "Comment 3")
        self.assertEqual(self.server.group_ids[1].cross_connect_server_group_id, 3)

        self.assertTrue(self.server.menu_id)
        self.assertTrue(self.server.web_icon_data)

    @patch("requests.request")
    def test_get_cross_connect_url(self, req):
        req.return_value = _mock_json(
            {
                "groups": [
                    {"id": 1, "name": "Test Group 1", "comment": "Comment 1"},
                    {"id": 2, "name": "Test Group 2", "comment": "Comment 2"},
                ]
            }
        )
        self.server.action_sync()

        user = self.env["res.users"].create(
            {
                "name": "Test User",
                "login": "test_user",
                "email": "test@example.com",
            }
        )
        group = self.server.group_ids[0]
        user.write({"groups_id": [(4, group.id)]})

        req.reset_mock()
        req.return_value = _mock_json({"client_id": 1, "token": "test-token"})

        self.assertEqual(
            self.server.with_user(user).sudo()._get_cross_connect_url(),
            "http://test-server.example.com/cross_connect/login/1/test-token",
        )

        req.assert_called_once_with(
            "POST",
            "http://test-server.example.com/cross_connect/access",
            headers={"api-key": "server-api-key"},
            json={
                "id": user.id,
                "name": "Test User",
                "login": "test_user",
                "email": "test@example.com",
                "lang": "en_US",
                "groups": [group.cross_connect_server_group_id],
            },
            timeout=10,
        )
        req.reset_mock()
        req.return_value = _mock_json({"client_id": 1})
        with self.assertRaisesRegex(UserError, "Missing token"):
            self.server.with_user(user).sudo()._get_cross_connect_url()

    @patch("requests.request")
    def test_get_cross_connect_url_bad_groups(self, req):
        req.return_value = _mock_json(
            {
                "groups": [
                    {"id": 1, "name": "Test Group 1", "comment": "Comment 1"},
                    {"id": 2, "name": "Test Group 2", "comment": "Comment 2"},
                ]
            }
        )
        self.server.action_sync()

        user = self.env["res.users"].create(
            {
                "name": "Test User",
                "login": "test_user",
                "email": "test@example.com",
            }
        )

        req.reset_mock()
        req.return_value = _mock_json({"client_id": 1, "token": "test-token"})

        with self.assertRaisesRegex(
            UserError, "You are not allowed to access this server"
        ):
            self.server.with_user(user).sudo()._get_cross_connect_url()


class TestCrossConnectClientController(HttpCase):
    def test_act_url_redirect(self):
        server = self.env["cross.connect.server"].create(
            {
                "name": "Test Server",
                "server_url": "http://test-server.example.com",
                "api_key": "server-api-key",
            }
        )
        with patch(
            "requests.request",
            return_value=_mock_json(
                {
                    "groups": [
                        {"id": 1, "name": "Test Group 1", "comment": "Comment 1"},
                        {"id": 2, "name": "Test Group 2", "comment": "Comment 2"},
                    ]
                }
            ),
        ):
            server.action_sync()

        user = self.env["res.users"].create(
            {
                "name": "Test User",
                "login": "test_user",
                "email": "test@example.com",
                "password": "user_pas$w0rd",
            }
        )
        group = server.group_ids[0]
        user.write({"groups_id": [(4, group.id)]})
        self.authenticate("test_user", "user_pas$w0rd")
        with patch(
            "requests.request",
            return_value=_mock_json({"client_id": 1, "token": "test-token"}),
        ):
            resp = self.url_open(server.menu_id.action.url, allow_redirects=False)
        resp.raise_for_status()
        self.assertEqual(resp.status_code, 303)
        self.assertEqual(
            resp.headers["Location"],
            "http://test-server.example.com/cross_connect/login/1/test-token",
        )

    def test_bad_server(self):
        self.assertFalse(self.env["cross.connect.server"].search([]))
        resp = self.url_open("/cross_connect_server/1", allow_redirects=False)
        self.assertEqual(resp.status_code, 400)
