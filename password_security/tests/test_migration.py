# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.modules.migration import load_script
from odoo.tests.common import TransactionCase


class PasswordSecurityMigration(TransactionCase):
    def test_01_migration(self):
        """Test the migration of the password_length value into minlength"""

        # minlength has default value
        ICP = self.env["ir.config_parameter"]
        old_value = ICP.get_param("auth_password_policy.minlength")

        if self.env["res.company"]._fields.get("password_length"):
            # set different password_length for multiple companies
            company1 = self.env["res.company"].create({"name": "company1"})
            company2 = self.env["res.company"].create({"name": "company2"})
            company3 = self.env["res.company"].create({"name": "company3"})
            company1.password_length = 8
            company2.password_length = 15
            company3.password_length = 11

            # run migration script
            mod = load_script(
                "password_security/migrations/16.0.1.0.0/pre-migration.py",
                "pre-migration",
            )
            mod.migrate(self.env.cr, "16.0.1.0.0")

            # minlength updated to maximum value
            new_value = ICP.get_param("auth_password_policy.minlength")
            self.assertNotEqual(int(old_value), 15)
            self.assertEqual(int(new_value), 15)
