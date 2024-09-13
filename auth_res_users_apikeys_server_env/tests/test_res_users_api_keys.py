# Copyright 2018 ACSONE SA/NV
# Copyright 2021 Camptocamp SA
# @author: Simone Orsi <simone.orsi@camptocamp.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from odoo.exceptions import AccessDenied
from odoo.tests.common import SavepointCase
from odoo.tools.config import config


class TestAuthApiKey(SavepointCase):
    @classmethod
    def setUpClass(cls, *args, **kwargs):
        super().setUpClass(*args, **kwargs)
        cls.demo_user = cls.env.ref("base.user_demo")
        cls.demo_user = cls.demo_user.with_user(cls.demo_user)
        cls.secret = (
            cls.env["res.users.apikeys"]
            .with_user(cls.demo_user)
            ._generate(
                f"rpc_{config.get('running_env','test')}",
                "Test JSONRPC api key",
            )
        )
        cls.api_key = cls.env["res.users.apikeys"].search(
            [("user_id", "=", cls.demo_user.id)], limit=1
        )

    def test_check_credentials_ok_any_scope(self):
        """test no regression"""
        self.api_key.scope = False
        self.assertEqual(
            self.demo_user._check_credentials(self.secret, {"interactive": True}),
            self.demo_user.id,
        )

    def test_check_credentials_ok(self):
        self.assertEqual(
            self.demo_user._check_credentials(self.secret, {"interactive": True}),
            self.demo_user.id,
        )

    def test_wrong_user(self):
        admin = self.env.ref("base.user_admin")
        with self.assertRaises(AccessDenied):
            admin.with_user(admin)._check_credentials(
                self.secret, {"interactive": True}
            ),

    def test_check_credentials_wrong_scope(self):
        self.api_key.scope = "rpc_wrong"
        with self.assertRaises(AccessDenied):
            self.demo_user._check_credentials(self.secret, {"interactive": True}),

    def test_check_credentials_no_api_keys(self):
        self.api_key.unlink()
        with self.assertRaises(AccessDenied):
            self.demo_user._check_credentials(self.secret, {"interactive": True}),
