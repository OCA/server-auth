# Copyright 2018 ACSONE SA/NV
# Copyright 2021 Camptocamp SA
# @author: Simone Orsi <simone.orsi@camptocamp.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase

from odoo.addons.server_environment import serv_config


class TestAuthApiKey(TransactionCase):
    @classmethod
    def setUpClass(cls, *args, **kwargs):
        super().setUpClass(*args, **kwargs)
        cls.AuthApiKey = cls.env["auth.api.key"]
        cls.demo_user = cls.env.ref("base.user_demo")
        cls.api_key_from_env = cls.AuthApiKey.create(
            {
                "name": "From Env",
                "key": "dummy",
                "user_id": cls.demo_user.id,
                "tech_name": "test_env",
            }
        )
        cls.api_key_from_env.invalidate_recordset()
        serv_config.add_section("api_key_test_env")
        serv_config.set("api_key_test_env", "key", "api_key_from_env")

    def test_lookup_key_from_env(self):
        self.assertEqual(
            self.env["auth.api.key"]._retrieve_uid_from_api_key("api_key_from_env"),
            self.demo_user.id,
        )
        with self.assertRaises(ValidationError):
            # dummy key must be replace with the one from env and
            # therefore should be unusable
            self.env["auth.api.key"]._retrieve_uid_from_api_key("dummy")
