# Copyright 2024 360ERP (<https://www.360erp.com>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)

import json
from uuid import uuid4

from lxml import etree

from odoo.exceptions import AccessError
from odoo.tests import HttpCase, tagged
from odoo.tools import mute_logger


@tagged("post_install", "-at_install")
class TestImpersonateLogin(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.admin_user = cls.env.ref("base.user_admin")
        cls.demo_user = cls.env.ref("base.user_demo")

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
            "/web/dataset/call_kw/res.partner/web_save",
            data=json.dumps(
                {
                    "params": {
                        "model": "res.partner",
                        "method": "web_save",
                        "args": [
                            [],
                            {
                                "name": "Contact123",
                            },
                            {},
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
        contact_id = result[0]["id"]

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
            "/web/dataset/call_kw/res.partner/web_save",
            data=json.dumps(
                {
                    "params": {
                        "model": "res.partner",
                        "method": "web_save",
                        "args": [
                            [contact.id],
                            {
                                "ref": "abc",
                            },
                            {},
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
        contact_id = result[0]["id"]

        self.assertEqual(contact.id, contact_id)
        self.assertEqual(contact.ref, "abc")
        self.assertEqual(contact.write_uid, self.admin_user)

    def test_05_create_uid_on_transient_model(self):
        """Check the create_uid of records created
        during an impersonated session on a transient model"""
        # Login as admin
        self.authenticate(user="admin", password="admin")

        # Impersonate demo user and create a wizard record
        self._impersonate_user(self.demo_user)

        response = self.url_open(
            "/web/dataset/call_kw/mail.wizard.invite/web_save",
            data=json.dumps(
                {
                    "params": {
                        "model": "mail.wizard.invite",
                        "method": "web_save",
                        "args": [
                            [],
                            {
                                "res_model": "res.partner",
                                "message": "Hello",
                            },
                            {},
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
        settings_id = result[0]["id"]

        wizard = self.env["mail.wizard.invite"].browse(settings_id)
        self.assertIn("Hello", wizard.message)
        self.assertEqual(wizard.create_uid, self.demo_user)

    def test_06_limit_access_to_admin(self):
        """
        Test restriction on impersonating admin users
        with 'Administration: Settings' access rights.
        """
        config_settings = self.env["res.config.settings"].create(
            {"restrict_impersonate_admin_settings": True}
        )
        config_settings.execute()

        config_restrict = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("impersonate_login.restrict_impersonate_admin_settings")
        )
        self.assertTrue(config_restrict)

        admin_settings_group = self.env.ref("base.group_system")
        self.admin_user.groups_id += admin_settings_group

        self.authenticate(user="demo", password="demo")
        self.assertEqual(self.session.uid, self.demo_user.id)

        self.demo_user.groups_id += self.env.ref(
            "impersonate_login.group_impersonate_login"
        )

        with mute_logger("odoo.http"):
            data = self._impersonate_user(self.admin_user)
        self.assertEqual(
            data["error"]["data"]["message"],
            "You cannot impersonate users with "
            "'Administration: Settings' access rights.",
        )

    def _demo_impersonator(self):
        self.demo_user.groups_id += self.env.ref(
            "impersonate_login.group_impersonate_login"
        )
        self.authenticate(user="demo", password="demo")
        self.assertEqual(self.session.uid, self.demo_user.id)

    def _restrict_admin_settings(self):
        self.env["ir.config_parameter"].sudo().set_param(
            "impersonate_login.restrict_impersonate_admin_settings", True
        )
        self.admin_user.groups_id += self.env.ref("base.group_system")

    def test_07_forbidden_user(self):
        """A user set to Forbidden can never be impersonated."""
        self.admin_user.impersonate_mode = "forbidden"
        self._demo_impersonator()
        with mute_logger("odoo.http"):
            data = self._impersonate_user(self.admin_user)
        self.assertEqual(
            data["error"]["data"]["message"], "This user cannot be impersonated."
        )
        self.assertEqual(self._get_session_info()["result"]["uid"], self.demo_user.id)

    def test_08_allowed_admin_despite_restriction(self):
        """An administrator set to Allowed can be impersonated even when the
        general setting restricts administrators."""
        self._restrict_admin_settings()
        self.admin_user.impersonate_mode = "allowed"
        self._demo_impersonator()
        data = self._impersonate_user(self.admin_user)
        self.assertNotIn("error", data)
        self.assertEqual(self._get_session_info()["result"]["uid"], self.admin_user.id)

    def test_09_default_admin_follows_restriction(self):
        """Default mode keeps the general setting."""
        self._restrict_admin_settings()
        self.assertEqual(self.admin_user.impersonate_mode, "default")
        self._demo_impersonator()
        with mute_logger("odoo.http"):
            data = self._impersonate_user(self.admin_user)
        self.assertEqual(
            data["error"]["data"]["message"],
            "You cannot impersonate users with "
            "'Administration: Settings' access rights.",
        )

    def test_10_only_administrators_set_the_mode(self):
        """A user cannot lift their own protection."""
        self.demo_user.impersonate_mode = "forbidden"
        with self.assertRaises(AccessError):
            self.demo_user.with_user(self.demo_user).write(
                {"impersonate_mode": "default"}
            )
        self.assertEqual(self.demo_user.impersonate_mode, "forbidden")

    def test_11_only_impersonable_users_are_listed(self):
        """The "Switch Login" list only shows users that can be impersonated."""
        self._restrict_admin_settings()
        forbidden = self.env["res.users"].create(
            {
                "name": "Forbidden User",
                "login": "forbidden_impersonate",
                "impersonate_mode": "forbidden",
            }
        )
        allowed_admin = self.env["res.users"].create(
            {
                "name": "Allowed Admin",
                "login": "allowed_admin_impersonate",
                "impersonate_mode": "allowed",
                "groups_id": [(4, self.env.ref("base.group_system").id)],
            }
        )
        self._demo_impersonator()
        domain = self._action_impersonate_login()["result"]["domain"]
        listed = self.env["res.users"].search(domain)
        self.assertIn(allowed_admin, listed)
        self.assertNotIn(forbidden, listed)
        self.assertNotIn(self.admin_user, listed)  # restricted administrator
        self.assertNotIn(self.demo_user, listed)  # oneself
        as_demo = self.env["res.users"].with_user(self.demo_user)
        self.assertFalse(as_demo.browse(forbidden.id).impersonate_allowed)
        self.assertFalse(as_demo.browse(self.admin_user.id).impersonate_allowed)
        self.assertFalse(as_demo.browse(self.demo_user.id).impersonate_allowed)
        self.assertTrue(as_demo.browse(allowed_admin.id).impersonate_allowed)

    def test_12_button_hidden_for_users_that_cannot_be_impersonated(self):
        """The row button of the users list follows impersonate_allowed."""
        arch = etree.fromstring(
            self.env["res.users"]
            .with_user(self.admin_user)
            .get_view(self.env.ref("base.view_users_tree").id, "list")["arch"]
        )
        buttons = arch.xpath("//button[@name='impersonate_login']")
        self.assertEqual(len(buttons), 1)
        self.assertEqual(buttons[0].get("invisible"), "not impersonate_allowed")
        self.assertTrue(arch.xpath("//field[@name='impersonate_allowed']"))
        # A non-administrator impersonator gets the same button and its field.
        impersonator = self.env["res.users"].create(
            {
                "name": "Impersonator",
                "login": "impersonator_view",
                "groups_id": [
                    (4, self.env.ref("base.group_user").id),
                    (4, self.env.ref("base.group_erp_manager").id),
                    (4, self.env.ref("impersonate_login.group_impersonate_login").id),
                ],
            }
        )
        view_id = self.env.ref("base.view_users_tree").id
        arch = etree.fromstring(
            self.env["res.users"]
            .with_user(impersonator)
            .get_view(view_id, "list")["arch"]
        )
        self.assertEqual(
            arch.xpath("//button[@name='impersonate_login']")[0].get("invisible"),
            "not impersonate_allowed",
        )
        # Without the group: neither the button nor the field.
        self.env.ref("impersonate_login.group_impersonate_login").users -= impersonator
        arch = etree.fromstring(
            self.env["res.users"]
            .with_user(impersonator)
            .get_view(view_id, "list")["arch"]
        )
        self.assertFalse(arch.xpath("//button[@name='impersonate_login']"))
        self.assertFalse(arch.xpath("//field[@name='impersonate_allowed']"))

    def _set_restriction(self, value):
        self.env["res.config.settings"].create(
            {"restrict_impersonate_admin_settings": value}
        ).set_values()

    def test_13_flag_and_list_follow_the_general_setting(self):
        """Changing the general setting in the settings changes both the flag
        (re-read in the same environment) and who is listed."""
        self.admin_user.groups_id += self.env.ref("base.group_system")
        users = self.env["res.users"].with_user(self.demo_user)
        target = users.browse(self.admin_user.id)
        allowed = [("impersonate_allowed", "=", True)]
        self._set_restriction(False)
        self.assertTrue(target.impersonate_allowed)
        self.assertIn(self.admin_user, users.search(allowed))
        self._set_restriction(True)
        self.assertFalse(target.impersonate_allowed)
        self.assertNotIn(self.admin_user, users.search(allowed))
        self._set_restriction(False)
        self.assertTrue(target.impersonate_allowed)
        self.assertIn(self.admin_user, users.search(allowed))

    def test_14_search_matches_the_computed_flag(self):
        """The SQL rule gives the same answer as the computed flag."""
        group_system = self.env.ref("base.group_system")
        implying = self.env["res.groups"].create(
            {"name": "Implies Settings", "implied_ids": [(4, group_system.id)]}
        )
        Users = self.env["res.users"]
        users = (
            self.env.ref("base.user_root")
            | self.admin_user
            | self.demo_user
            | Users.create({"name": "Plain", "login": "plain_imp"})
            | Users.create(
                {"name": "Implied Admin", "login": "implied_imp", "groups_id": implying}
            )
            | Users.create(
                {"name": "Inactive Admin", "login": "inactive_imp", "active": False}
            )
            | Users.create(
                {
                    "name": "Forbidden",
                    "login": "forbidden_imp",
                    "impersonate_mode": "forbidden",
                }
            )
            | Users.create(
                {
                    "name": "Allowed Admin",
                    "login": "allowed_imp",
                    "impersonate_mode": "allowed",
                    "groups_id": group_system,
                }
            )
        )
        users.filtered(lambda u: u.login == "inactive_imp").groups_id += group_system
        as_demo = Users.with_user(self.demo_user).with_context(active_test=False)
        for restrict in (False, True):
            self._set_restriction(restrict)
            for user in users:
                with self.subTest(restrict=restrict, login=user.login):
                    flag = as_demo.browse(user.id).impersonate_allowed
                    ids = [("id", "=", user.id)]
                    for operator, value, expected in (
                        ("=", True, flag),
                        ("!=", True, not flag),
                        ("=", False, not flag),
                        ("!=", False, flag),
                    ):
                        found = as_demo.search(
                            ids + [("impersonate_allowed", operator, value)]
                        )
                        self.assertEqual(bool(found), expected, (operator, value))
