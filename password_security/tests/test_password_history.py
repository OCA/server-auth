# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class TestPasswordHistory(TransactionCase):
    def test_check_password_history(self):
        # Disable all password checks except for history
        set_param = self.env["ir.config_parameter"].sudo().set_param
        set_param("auth_password_policy.minlength", 0)
        user = self.env.ref("base.user_admin")
        user.company_id.update(
            {
                "password_policy_enabled": True,
                "password_estimate": 0,
                "password_length": 0,
                "password_lower": 0,
                "password_history": 1,
                "password_numeric": 0,
                "password_special": 0,
                "password_upper": 0,
            }
        )

        self.assertEqual(len(user.password_history_ids), 0)

        user.write({"password": "admin"})
        self.assertEqual(len(user.password_history_ids), 1)

        with self.assertRaises(UserError):
            user.write({"password": "admin"})
        user.write({"password": "admit"})
        self.assertEqual(len(user.password_history_ids), 2)

        user.company_id.password_history = 2
        with self.assertRaises(UserError):
            user.write({"password": "admin"})
        with self.assertRaises(UserError):
            user.write({"password": "admit"})
        user.write({"password": "badminton"})
        self.assertEqual(len(user.password_history_ids), 3)

        user.company_id.password_history = 0
        user.write({"password": "badminton"})
        self.assertEqual(len(user.password_history_ids), 4)

        user.company_id.password_history = -1
        with self.assertRaises(UserError):
            user.write({"password": "admin"})
