# Copyright 2026 360ERP (<https://www.360erp.com>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase

from odoo.addons.auth_user_role.hooks import post_init_hook


class TestHooks(TransactionCase):
    def test_post_init_hook_creates_param(self):
        """Test that the hook creates the parameter if it is missing."""
        param_key = "auth_user_role.strict_sync"

        # Ensure the parameter is completely removed
        self.env["ir.config_parameter"].sudo().search(
            [("key", "=", param_key)]
        ).unlink()

        # Run the hook manually
        post_init_hook(self.env)

        # Verify it was created and set to 'True'
        val = self.env["ir.config_parameter"].sudo().get_param(param_key)
        self.assertEqual(val, "True")

    def test_post_init_hook_respects_existing_param(self):
        """Test that the hook does NOT overwrite an existing parameter."""
        param_key = "auth_user_role.strict_sync"

        # Explicitly set the parameter to 'False' before the hook runs
        self.env["ir.config_parameter"].sudo().set_param(param_key, "False")

        # Run the hook manually
        post_init_hook(self.env)

        # Verify the hook respected the existing 'False' value
        val = self.env["ir.config_parameter"].sudo().get_param(param_key)
        self.assertEqual(val, "False")
