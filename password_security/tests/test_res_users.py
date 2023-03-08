# Copyright 2015 LasLabs Inc.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo.exceptions import UserError
from odoo.tests.common import SavepointCase


class TestResUsers(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super(TestResUsers, cls).setUpClass()
        cls.login = "foslabs@example.com"
        cls.partner_vals = {
            "name": "Partner",
            "is_company": False,
            "email": cls.login,
        }
        cls.password = "asdQWE123$%^"
        cls.main_comp = cls.env.ref("base.main_company")
        cls.vals = {
            "name": "User",
            "login": cls.login,
            "password": cls.password,
            "company_id": cls.main_comp.id,
        }
        cls.model_obj = cls.env["res.users"]
        cls.rec_id = cls._new_record()

    @classmethod
    def _new_record(cls):
        partner_id = cls.env["res.partner"].create(cls.partner_vals)
        cls.vals["partner_id"] = partner_id.id
        return cls.model_obj.create(cls.vals)

    def test_password_write_date_is_saved_on_create(self):
        self.assertTrue(
            self.rec_id.password_write_date,
            "Password write date was not saved to db.",
        )

    def test_password_write_date_is_updated_on_write(self):
        self.rec_id.write({"password_write_date": "1970-01-01 00:00:00"})
        old_write_date = self.rec_id.password_write_date
        self.rec_id.write({"password": "asdQWE123$%^2"})
        new_write_date = self.rec_id.password_write_date
        self.assertNotEqual(
            old_write_date,
            new_write_date,
            "Password write date was not updated on write.",
        )

    def test_does_not_update_write_date_if_password_unchanged(self):
        self.rec_id.write({"password_write_date": "1970-01-01 00:00:00"})
        old_write_date = self.rec_id.password_write_date
        self.rec_id.write({"name": "Luser"})
        new_write_date = self.rec_id.password_write_date
        self.assertEqual(
            old_write_date,
            new_write_date,
            "Password not changed but write date updated anyway.",
        )

    def test_check_password_returns_true_for_valid_password(self):
        self.assertTrue(
            self.rec_id._check_password("asdQWE123$%^3"),
            "Password is valid but check failed.",
        )

    def test_check_password_raises_error_for_invalid_password(self):
        with self.assertRaises(UserError):
            self.rec_id._check_password("password")

    def test_save_password_crypt(self):
        self.assertEqual(
            1,
            len(self.rec_id.password_history_ids),
        )

    def test_check_password_crypt(self):
        """It should raise UserError if previously used"""
        with self.assertRaises(UserError):
            self.rec_id.write({"password": self.password})

    def test_password_is_expired_if_record_has_no_write_date(self):
        self.rec_id.write({"password_write_date": None})
        self.assertTrue(
            self.rec_id._password_has_expired(),
            "Record has no password write date but check failed.",
        )

    def test_an_old_password_is_expired(self):
        old_write_date = "1970-01-01 00:00:00"
        self.rec_id.write({"password_write_date": old_write_date})
        self.assertTrue(
            self.rec_id._password_has_expired(),
            "Password is out of date but check failed.",
        )

    def test_a_new_password_is_not_expired(self):
        self.assertFalse(
            self.rec_id._password_has_expired(),
            "Password was just created but has already expired.",
        )

    def test_expire_password_generates_token(self):
        self.rec_id.sudo().action_expire_password()
        token = self.rec_id.partner_id.signup_token
        self.assertTrue(
            token,
            "A token was not generated.",
        )

    def test_validate_pass_reset_error(self):
        """It should throw UserError on reset inside min threshold"""
        with self.assertRaises(UserError):
            self.rec_id._validate_pass_reset()

    def test_validate_pass_reset_allow(self):
        """It should allow reset pass when outside threshold"""
        self.rec_id.password_write_date = "2016-01-01"
        self.assertEqual(
            True,
            self.rec_id._validate_pass_reset(),
        )

    def test_validate_pass_reset_zero(self):
        """It should allow reset pass when <= 0"""
        self.rec_id.company_id.password_minimum = 0
        self.assertEqual(
            True,
            self.rec_id._validate_pass_reset(),
        )

    def test_underscore_is_special_character(self):
        self.assertTrue(self.main_comp.password_special)
        self.rec_id._check_password("asdQWE12345_3")

    def test_user_with_admin_rights_can_create_users(self):
        demo = self.env.ref("base.user_demo")
        demo.groups_id |= self.env.ref("base.group_erp_manager")
        test1 = self.model_obj.with_user(demo).create(
            {
                "login": "test1",
                "name": "test1",
            }
        )
        test1.unlink()
