# Copyright 2021 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo.exceptions import UserError

from odoo.addons.base.tests.common import SavepointCaseWithUserDemo


class TestUserEmptyPassword(SavepointCaseWithUserDemo):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.wizard_model = cls.env["empty.password.wizard"]

    def test_empty_password_button(self):
        """Test that the wizard's default_get correctly assigns user_ids."""
        context = {
            "active_model": "res.users",
            "active_ids": [self.user_demo.id],
        }

        wizard = self.wizard_model.with_context(**context).create({})

        wizard.empty_password_button()

        self.assertIn(self.user_demo, wizard.user_ids)
        self.assertFalse(self.user_demo.has_password)

    def test_invalid_model(self):
        """Test that the wizard raises a UserError
        when active_model is not res.users.
        """
        context = {
            "active_model": "res.partner",
            "active_ids": [self.user_demo.id],
        }

        with self.assertRaises(UserError):
            self.wizard_model.with_context(**context).create({})
