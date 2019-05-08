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
        serv_config.add_section("api_key_inactive_ok")
        serv_config.set("api_key_inactive_ok", "user", "demo")
        serv_config.set("api_key_inactive_ok", "key", "api_inactive_ok_key")
        serv_config.set("api_key_inactive_ok", "allow_inactive_user", "True")
        serv_config.add_section("api_key_inactive_nok")
        serv_config.set("api_key_inactive_nok", "user", "demo")
        serv_config.set("api_key_inactive_nok", "key", "api_inactive_nok_key")
        serv_config.set("api_key_inactive_nok", "allow_inactive_user", "False")
        serv_config.add_section("api_key_inactive_off")
        serv_config.set("api_key_inactive_off", "user", "demo")
        serv_config.set("api_key_inactive_off", "key", "api_inactive_off_key")

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

    def test_user_inactive_allowed(self):
        demo_user = self.env.ref("base.user_demo")
        demo_user.write({'active': False})
        self.assertEqual(
            self.env["auth.api.key"]._retrieve_uid_from_api_key(
                "api_inactive_ok_key"),
            demo_user.id,
        )

    def test_user_inactive_not_allowed(self):
        demo_user = self.env.ref("base.user_demo")
        demo_user.write({'active': False})
        with self.assertRaises(ValidationError):
            self.env["auth.api.key"].\
                _retrieve_uid_from_api_key("api_inactive_nok_key")

    def test_user_inactive_not_specified(self):
        demo_user = self.env.ref("base.user_demo")
        demo_user.write({'active': False})
        with self.assertRaises(ValidationError):
            self.env["auth.api.key"].\
                _retrieve_uid_from_api_key("api_inactive_off_key")
