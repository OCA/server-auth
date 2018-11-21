# -*- coding: utf-8 -*-
# Copyright 2018 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from odoo.tests.common import TransactionCase
from odoo.addons.server_environment import serv_config
from odoo.exceptions import ValidationError, AccessError


class TestAuthApiKey(TransactionCase):
    @classmethod
    def setUpClass(cls, *args, **kwargs):
        super(TestAuthApiKey, cls).setUpClass(*args, **kwargs)

        serv_config.add_section("api_key_good")
        serv_config.set("api_key_good", "user", "demo")
        serv_config.set("api_key_good", "key", "api_right_key")
        serv_config.add_section("api_key_bad")
        serv_config.set("api_key_bad", "user", "not_demo")
        serv_config.set("api_key_bad", "key", "api_wrong_key")

    def test_lookup(self):
        demo_user = self.env.ref("base.user_demo")
        self.assertEqual(
            self.env["auth.api.key"]._retrieve_uid_from_api_key(
                "api_right_key"),
            demo_user.id,
        )

    def test_wrong_key(self):
        with self.assertRaises(ValidationError), self.env.cr.savepoint():
            self.env["auth.api.key"]._retrieve_uid_from_api_key(
                "api_wrong_key")

    def test_user_not_allowed(self):
        demo_user = self.env.ref("base.user_demo")
        with self.assertRaises(AccessError), self.env.cr.savepoint():
            self.env["auth.api.key"].sudo(user=demo_user).\
                _retrieve_uid_from_api_key("api_wrong_key")
