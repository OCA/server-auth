# Copyright 2023 Onestein (<https://www.onestein.eu>)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestConfigSettings(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.config = cls.env["res.config.settings"].create({})

    def test_01_password_estimate_range(self):
        """The estimation must be between 0 and 4"""
        self.config.password_estimate = 0
        self.config.password_estimate = 2
        self.config.password_estimate = 4

        with self.assertRaises(ValidationError):
            self.config.password_estimate = 5

        with self.assertRaises(ValidationError):
            self.config.password_estimate = -1
