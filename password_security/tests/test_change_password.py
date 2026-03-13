# Copyright 2023 Onestein (<https://www.onestein.eu>)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo.exceptions import UserError, ValidationError
from odoo.tests.common import TransactionCase, new_test_user


class TestChangePassword(TransactionCase):
    def setUp(self):
        super().setUp()
        self.username = "jackoneill"
        self.passwd = "!asdQWE12345_3"
        self.user = new_test_user(self.env, self.username, password=self.passwd)

    def test_01_change_password_fail(self):
        """Doit échouer si le nouveau mot de passe est trop faible."""
        with self.assertRaises(ValidationError):
            self.user.password = "jackoneill"

    def test_02_change_password_success(self):
        """Doit réussir avec un mot de passe fort."""
        self.user.password = "!asdQWE12345_4"

    def test_03_change_password_history(self):
        """Doit interdire la réutilisation d'un ancien mot de passe."""
        with self.assertRaises(UserError):
            self.user.password = self.passwd
