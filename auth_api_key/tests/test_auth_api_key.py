# Copyright 2018 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from odoo.exceptions import AccessError, ValidationError
from odoo.tests.common import TransactionCase


class TestAuthApiKey(TransactionCase):
    @classmethod
    def setUpClass(cls, *args, **kwargs):
        super().setUpClass(*args, **kwargs)
        cls.AuthApiKey = cls.env["auth.api.key"]
        cls.demo_user = cls.env.ref("base.user_demo")
        cls.api_key_good = cls.AuthApiKey.create(
            {"name": "good", "user_id": cls.demo_user.id, "key": "api_key"}
        )

    def test_lookup_key_from_db(self):
        demo_user = self.env.ref("base.user_demo")
        self.assertEqual(
            self.env["auth.api.key"]._retrieve_uid_from_api_key("api_key"), demo_user.id
        )

    def test_wrong_key(self):
        with self.assertRaises(ValidationError), self.env.cr.savepoint():
            self.env["auth.api.key"]._retrieve_uid_from_api_key("api_wrong_key")

    def test_user_not_allowed(self):
        # only system users can check for key
        with self.assertRaises(AccessError), self.env.cr.savepoint():
            self.env["auth.api.key"].with_user(
                user=self.demo_user
            )._retrieve_uid_from_api_key("api_wrong_key")

    def test_cache_invalidation(self):
        self.assertEqual(
            self.env["auth.api.key"]._retrieve_uid_from_api_key("api_key"),
            self.demo_user.id,
        )
        self.api_key_good.write({"key": "updated_key"})
        self.assertEqual(
            self.env["auth.api.key"]._retrieve_uid_from_api_key("updated_key"),
            self.demo_user.id,
        )
        with self.assertRaises(ValidationError):
            self.env["auth.api.key"]._retrieve_uid_from_api_key("api_key")

    def test_user_archived_unarchived_with_option_on(self):
        self.env.company.archived_user_disable_auth_api_key = True
        demo_user = self.env.ref("base.user_demo")
        self.assertEqual(
            self.env["auth.api.key"]._retrieve_uid_from_api_key("api_key"), demo_user.id
        )
        demo_user.active = False
        with self.assertRaises(ValidationError):
            self.env["auth.api.key"]._retrieve_uid_from_api_key("api_key")
        demo_user.active = True
        self.assertEqual(
            self.env["auth.api.key"]._retrieve_uid_from_api_key("api_key"), demo_user.id
        )

    def test_user_archived_unarchived_with_option_off(self):
        self.env.company.archived_user_disable_auth_api_key = False
        demo_user = self.env.ref("base.user_demo")
        self.assertEqual(
            self.env["auth.api.key"]._retrieve_uid_from_api_key("api_key"), demo_user.id
        )
        demo_user.active = False
        self.assertEqual(
            self.env["auth.api.key"]._retrieve_uid_from_api_key("api_key"), demo_user.id
        )
