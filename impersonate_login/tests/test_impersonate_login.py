# Copyright 2024 360ERP (<https://www.360erp.com>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)

import json
from uuid import uuid4

from odoo.tests import HttpCase, tagged
from odoo.tools import mute_logger


@tagged("post_install", "-at_install")
class TestImpersonateLogin(HttpCase):
    def setUp(self):
        super().setUp()
        self.admin_user = self.env.ref("base.user_admin")
        self.demo_user = self.env.ref("base.user_demo")

    def _impersonate_user(self, user):
        response = self.url_open(
            "/web/dataset/call_button",
            data=json.dumps(
                {
                    "params": {
                        "model": "res.users",
                        "method": "impersonate_login",
                        "args": [user.id],
                        "kwargs": {},
                    },
                }
            ),
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(response.status_code, 200)
        return response.json()

    def _action_impersonate_login(self):
        response = self.url_open(
            "/web/dataset/call_button",
            data=json.dumps(
                {
                    "params": {
                        "model": "res.users",
                        "method": "action_impersonate_login",
                        "args": [],
                        "kwargs": {},
                    },
                }
            ),
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(response.status_code, 200)
        return response.json()

    def _get_session_info(self):
        response = self.url_open(
            "/web/session/get_session_info",
            data=json.dumps(dict(jsonrpc="2.0", method="call", id=str(uuid4()))),
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(response.status_code, 200)
        return response.json()

    def test_01_admin_impersonates_user_demo(self):
        """Admin user impersonates Demo user"""
        # Login as admin
        self.authenticate(user="admin", password="admin")
        self.assertEqual(self.session.uid, self.admin_user.id)

        # Check get_session_info()
        data = self._get_session_info()
        result = data["result"]
        self.assertEqual(result["username"], self.admin_user.login)
        self.assertTrue(result["is_system"])
        self.assertTrue(result["is_admin"])
        self.assertTrue(result["is_impersonate_user"])
        self.assertFalse(result["impersonate_from_uid"])

        # Switch Login button
        data = self._action_impersonate_login()
        result = data["result"]
        self.assertEqual(result["target"], "new")

        # Impersonate demo user
        data = self._impersonate_user(self.demo_user)
        result = data["result"]
        self.assertEqual(result["tag"], "reload")

        # Check get_session_info()
        data = self._get_session_info()
        result = data["result"]
        self.assertEqual(result["username"], self.demo_user.login)
        self.assertFalse(result["is_system"])
        self.assertFalse(result["is_admin"])
        self.assertFalse(result["is_impersonate_user"])
        self.assertEqual(result["impersonate_from_uid"], self.admin_user.id)

        # Check impersonate log
        log1 = self.env["impersonate.log"].search([], order="id desc", limit=1)
        self.assertTrue(log1.date_start)
        self.assertFalse(log1.date_end)

        # Impersonate demo user again: error
        with mute_logger("odoo.http"):
            data = self._impersonate_user(self.demo_user)
        result = data["error"]
        self.assertEqual(
            result["data"]["message"], "You are already Logged as another user."
        )

        # Back to original user
        data = self._impersonate_user(self.admin_user)
        result = data["result"]
        self.assertEqual(result["tag"], "reload")

        # Check get_session_info()
        data = self._get_session_info()
        result = data["result"]
        self.assertEqual(result["username"], self.admin_user.login)
        self.assertTrue(result["is_system"])
        self.assertTrue(result["is_admin"])
        self.assertTrue(result["is_impersonate_user"])
        self.assertFalse(result["impersonate_from_uid"])

        # Check impersonate log
        log2 = self.env["impersonate.log"].search([], order="id desc", limit=1)
        # Refresh the log1 after the attribute date_end is updated
        log1.refresh()
        self.assertEqual(log1, log2)
        self.assertTrue(log1.date_start)
        self.assertTrue(log1.date_end)

    def test_02_user_demo_impersonates_admin(self):
        """Demo user impersonates Admin user"""
        # Login as demo user
        self.authenticate(user="demo", password="demo")
        self.assertEqual(self.session.uid, self.demo_user.id)

        # Check get_session_info()
        data = self._get_session_info()
        result = data["result"]
        self.assertFalse(result["is_impersonate_user"])
        self.assertFalse(result["impersonate_from_uid"])

        # Impersonate demo user: is already current user
        self.demo_user.groups_id += self.env.ref(
            "impersonate_login.group_impersonate_login"
        )
        with mute_logger("odoo.http"):
            data = self._impersonate_user(self.demo_user)
        result = data["error"]
        self.assertEqual(result["data"]["message"], "It's you.")

        # Impersonate admin user
        data = self._impersonate_user(self.admin_user)
        result = data["result"]
        self.assertEqual(result["tag"], "reload")

        # Check get_session_info()
        data = self._get_session_info()
        result = data["result"]
        self.assertEqual(result["username"], self.admin_user.login)
        self.assertTrue(result["is_system"])
        self.assertTrue(result["is_admin"])
        self.assertTrue(result["is_impersonate_user"])
        self.assertEqual(result["impersonate_from_uid"], self.demo_user.id)

        # Impersonate admin user again: error
        with mute_logger("odoo.http"):
            data = self._impersonate_user(self.admin_user)
        result = data["error"]
        self.assertEqual(
            result["data"]["message"], "You are already Logged as another user."
        )

        # Back to original user
        data = self._impersonate_user(self.demo_user)
        result = data["result"]
        self.assertEqual(result["tag"], "reload")

        # Check get_session_info()
        data = self._get_session_info()
        result = data["result"]
        self.assertEqual(result["username"], self.demo_user.login)
        self.assertFalse(result["is_system"])
        self.assertFalse(result["is_admin"])
        self.assertTrue(result["is_impersonate_user"])
        self.assertFalse(result["impersonate_from_uid"])

    def test_03_create_uid(self):
        """Check the create_uid of records created
        during an impersonated session"""
        # Login as admin
        self.authenticate(user="admin", password="admin")

        # Impersonate demo user and create a contact
        self._impersonate_user(self.demo_user)

        response = self.url_open(
            "/web/dataset/call_kw/res.partner/create",
            data=json.dumps(
                {
                    "params": {
                        "model": "res.partner",
                        "method": "create",
                        "args": [
                            {
                                "name": "Contact123",
                            },
                        ],
                        "kwargs": {},
                    },
                }
            ),
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        contact_id = data["result"]

        contact = self.env["res.partner"].browse(contact_id)
        self.assertEqual(contact.name, "Contact123")
        self.assertEqual(contact.create_uid, self.admin_user)

    def test_04_write_uid(self):
        """Check the write_uid of records created
        during an impersonated session"""
        # Login as admin
        self.authenticate(user="admin", password="admin")

        # Create a contact
        contact = self.env["res.partner"].create({"name": "ContactABC"})

        # Impersonate demo user and modify a contact
        self._impersonate_user(self.demo_user)

        response = self.url_open(
            "/web/dataset/call_kw/res.partner/write",
            data=json.dumps(
                {
                    "params": {
                        "model": "res.partner",
                        "method": "write",
                        "args": [
                            [contact.id],
                            {
                                "ref": "abc",
                            },
                        ],
                        "kwargs": {},
                    },
                }
            ),
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        result = data["result"]

        # Refresh contact to reflect changes in the database
        self.assertEqual(result, True)
        contact.invalidate_cache()
        self.assertEqual(contact.ref, "abc")
        self.assertEqual(contact.write_uid, self.admin_user)

    def test_05_limit_access_to_admin(self):
        """
        Test restriction on impersonating admin users
        with 'Administration: Settings' access rights.
        """
        # Enable the configuration setting via ResConfigSettings
        config_settings = self.env["res.config.settings"].create(
            {"restrict_impersonate_admin_settings": True}
        )
        config_settings.execute()

        # Ensure the configuration parameter is set
        config_restrict = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("impersonate_login.restrict_impersonate_admin_settings")
        )
        self.assertTrue(config_restrict)

        # Ensure the admin user has the 'Administration: Settings' group
        admin_settings_group = self.env.ref("base.group_system")
        self.admin_user.groups_id += admin_settings_group

        # Login as demo user
        self.authenticate(user="demo", password="demo")
        self.assertEqual(self.session.uid, self.demo_user.id)

        # Give demo user the impersonation group
        self.demo_user.groups_id += self.env.ref(
            "impersonate_login.group_impersonate_login"
        )

        with mute_logger("odoo.http"):
            data = self._impersonate_user(self.admin_user)
        # Validate the error message
        self.assertEqual(
            data["error"]["data"]["message"],
            "You cannot impersonate users with 'Administration: Settings' access rights.",
        )
