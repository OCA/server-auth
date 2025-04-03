# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class TestPasswordHistory(TransactionCase):
    def test_check_password_history(self):
        # Disable all password checks except for history
        set_param = self.env["ir.config_parameter"].sudo().set_param
        set_param("auth_password_policy.minlength", 0)
        user = self.env.ref("base.user_admin")
        param = self.env["ir.config_parameter"].sudo()
        param.set_param("password_security.history", 1)
        param.set_param("password_security.lower", 0)
        param.set_param("password_security.numeric", 0)
        param.set_param("password_security.special", 0)
        param.set_param("password_security.upper", 0)

        self.assertEqual(len(user.password_history_ids), 0)

        user.write({"password": "admin"})
        self.assertEqual(len(user.password_history_ids), 1)

        with self.assertRaises(UserError):
            user.write({"password": "admin"})
        user.write({"password": "admit"})
        self.assertEqual(len(user.password_history_ids), 2)

        param.set_param("password_security.history", 2)
        with self.assertRaises(UserError):
            user.write({"password": "admin"})
        with self.assertRaises(UserError):
            user.write({"password": "admit"})
        user.write({"password": "badminton"})
        self.assertEqual(len(user.password_history_ids), 3)

        param.set_param("password_security.history", 0)
        user.write({"password": "badminton"})
        self.assertEqual(len(user.password_history_ids), 4)

        param.set_param("password_security.history", -1)
        with self.assertRaises(UserError):
            user.write({"password": "admin"})
