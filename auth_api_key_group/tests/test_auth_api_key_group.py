# Copyright 2021 Camptocamp SA
# @author: Simone Orsi <simone.orsi@camptocamp.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).


from odoo.tests.common import TransactionCase


class TestAuthApiKey(TransactionCase):
    @classmethod
    def setUpClass(cls, *args, **kwargs):
        super().setUpClass(*args, **kwargs)
        cls.AuthApiKey = cls.env["auth.api.key"]
        cls.AuthApiKeyGroup = cls.env["auth.api.key.group"]
        cls.demo_user = cls.env.ref("base.user_demo")
        cls.api_key1 = cls.AuthApiKey.create(
            {"name": "One", "user_id": cls.demo_user.id, "key": "one"}
        )
        cls.api_key2 = cls.AuthApiKey.create(
            {"name": "Two", "user_id": cls.demo_user.id, "key": "two"}
        )
        cls.api_key3 = cls.AuthApiKey.create(
            {"name": "Three", "user_id": cls.demo_user.id, "key": "three"}
        )
        cls.api_key_group1 = cls.AuthApiKeyGroup.create(
            {
                "name": "G One",
                "code": "g-one",
                "auth_api_key_ids": [(6, 0, (cls.api_key1 + cls.api_key2).ids)],
            }
        )
        cls.api_key_group2 = cls.AuthApiKeyGroup.create(
            {
                "name": "G Two",
                "code": "g-two",
                "auth_api_key_ids": [(6, 0, cls.api_key3.ids)],
            }
        )

    def test_relations(self):
        self.assertIn(self.api_key_group1, self.api_key1.auth_api_key_group_ids)
        self.assertIn(self.api_key_group1, self.api_key2.auth_api_key_group_ids)
        self.assertNotIn(self.api_key_group1, self.api_key3.auth_api_key_group_ids)
        self.assertIn(self.api_key_group2, self.api_key3.auth_api_key_group_ids)
        self.assertNotIn(self.api_key_group2, self.api_key1.auth_api_key_group_ids)
        self.assertNotIn(self.api_key_group2, self.api_key1.auth_api_key_group_ids)
